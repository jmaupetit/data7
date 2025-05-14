"""Data7 application module."""

import contextlib
import importlib.metadata
import logging
from pathlib import PurePath
from typing import Callable, Generator, List, Optional, Tuple

import sentry_sdk
from pyinstrument import Profiler
from sentry_sdk.integrations.starlette import StarletteIntegration
from sqlalchemy import Engine, create_engine
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, StreamingResponse
from starlette.routing import Route
from starlette.status import HTTP_501_NOT_IMPLEMENTED

from .config import settings
from .models import Dataset, Extension, MimeType
from .streamers import sql2csv, sql2parquet
from .utils import populate_datasets

logger = logging.getLogger(__name__)


def get_dataset_from_url(
    url_path: PurePath, datasets: List[Dataset]
) -> Tuple[Dataset, Extension]:
    """Get dataset and extension from query URL path."""
    basename, ext = url_path.name.split(".")
    try:
        extension = Extension[ext.upper()]
    except KeyError as exc:
        raise ValueError(f"Data7 extension '{ext}' is not supported") from exc

    dataset = next((d for d in datasets if d.basename == basename), None)

    if dataset is None:
        raise ValueError("Requested dataset is not registered")

    return dataset, extension


def get_routes_from_datasets(datasets):
    """Get routes from datasets."""
    return [
        Route(
            f"{settings.datasets_root_url}/{dataset.basename}.{extension}",
            stream_dataset,
        )
        for dataset in datasets
        for extension in Extension
    ]


async def stream_dataset(request: Request) -> StreamingResponse:
    """Stream given dataset."""
    try:
        dataset, extension = get_dataset_from_url(
            PurePath(request.url.path), app.state.datasets
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_501_NOT_IMPLEMENTED, detail=str(exc)
        ) from exc
    media_type = MimeType[extension.name]

    streamer: Optional[Callable[[Engine, Dataset, int], Generator]] = None
    if extension == Extension.CSV:
        streamer = sql2csv
    elif extension == Extension.PARQUET:
        streamer = sql2parquet
    if streamer is None:
        raise HTTPException(
            status_code=HTTP_501_NOT_IMPLEMENTED,
            detail=f"Streamer for extension '{extension}' does not exist",
        )

    return StreamingResponse(
        streamer(engine, dataset, chunksize=settings.CHUNK_SIZE),
        media_type=media_type,
    )


# Database
logger.debug(f"{settings.DATABASE_URL=}")
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=settings.db_pool_check,
    pool_recycle=settings.db_pool_recycle,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_pool_max_overflow,
)

# Routes
routes = get_routes_from_datasets(settings.datasets)
logger.debug("Registered routes:\n%s", "\n".join([route.path for route in routes]))


# Middlewares
class ProfilingMiddleware(BaseHTTPMiddleware):
    """A pyinstrument request profiler middleware.

    The profiling middleware is active if the `profiling` setting is set to True.
    To activate the profiler on an HTTP request, you should also set the `profile`
    GET parameter to `1`.
    """

    async def dispatch(self, request, call_next):
        """Profile HTTP request."""
        if not request.query_params.get("profile", False):
            return await call_next(request)

        profiler = Profiler(
            interval=settings.PROFILER_INTERVAL,
            async_mode=settings.PROFILER_ASYNC_MODE,
        )
        profiler.start()
        response = await call_next(request)

        # As we use a StreamingResponse, we need to consume the iterator
        async for _ in response.body_iterator:
            pass

        profiler.stop()
        return HTMLResponse(profiler.output_html())


# App
@contextlib.asynccontextmanager
async def lifespan(app):
    """Application lifespan."""
    app.state.datasets = populate_datasets(engine)

    if settings.SENTRY_DSN is not None:
        sentry_sdk.init(
            dsn=str(settings.SENTRY_DSN),
            enable_tracing=settings.SENTRY_ENABLE_TRACING,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            release=importlib.metadata.version("data7"),
            environment=settings.EXECUTION_ENVIRONMENT,
            integrations=[
                StarletteIntegration(),
            ],
        )

    yield
    engine.dispose()


middleware = [Middleware(GZipMiddleware, minimum_size=1000)]
if settings.profiling:
    middleware += [Middleware(ProfilingMiddleware)]

logger.info("Active extensions: %s", ", ".join(e for e in Extension))

app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
    debug=settings.DEBUG,
)
