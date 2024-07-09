"""Data7 application module."""

import contextlib
import importlib.metadata
import logging
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from pathlib import PurePath
from typing import Callable, Generator, List, Optional, Tuple

import pandas as pd
import pyarrow as pa
import sentry_sdk
from pyarrow import parquet as pq
from pyinstrument import Profiler
from sentry_sdk.integrations.starlette import StarletteIntegration
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
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

logger = logging.getLogger(__name__)


@dataclass
class Dataset:
    """Dataset model."""

    basename: str
    query: str
    # Indexes can be defined for a dataset query
    indexes: Optional[List[str]] = None


class Extension(StrEnum):
    """Supported formats extensions."""

    CSV = "csv"
    PARQUET = "parquet"


class MimeType(StrEnum):
    """MimeTypes for supported formats."""

    CSV = "text/csv"
    PARQUET = "application/vnd.apache.parquet"


def populate_datasets() -> List[Dataset]:
    """Validate configured datasets and get sql query expected field names."""
    logging.debug("Will populate datasets given configuration...")
    datasets = []

    with engine.connect() as conn:
        for raw_dataset in settings.datasets:
            dataset = Dataset(**raw_dataset)

            # Validate database query and get expected field names
            try:
                result = conn.execute(text(dataset.query))
            except OperationalError as exc:
                raise ValueError(
                    f"Dataset '{dataset.basename}' query failed, maybe SQL is invalid"
                ) from exc

            # Query returns no result, we cannot set fields.
            if result.scalar() is None:
                logger.warning(
                    "'%s' query returned no result, dataset will be ignored",
                    dataset.basename,
                )
                continue

            datasets.append(dataset)

    logger.info("Active datasets: %s", ", ".join(d.basename for d in datasets))
    return datasets


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


def sql2parquet(dataset: Dataset, chunksize: int = 5000) -> Generator:
    """Stream SQL rows to parquet."""
    logger.debug("SQL query: %s", dataset.query)
    output = BytesIO()

    def get_batch(output: BytesIO) -> bytes:
        """Get wrote batch content."""
        size = output.tell()
        output.seek(0)
        return output.read(size)

    with engine.connect() as conn:
        # Get schema from a subset of data
        schema = pa.Schema.from_pandas(
            next(
                pd.read_sql_query(
                    dataset.query,
                    conn,
                    chunksize=settings.SCHEMA_SNIFFER_SIZE,
                    dtype_backend=settings.DEFAULT_DTYPE_BACKEND,
                    index_col=dataset.indexes,
                )
            )
        )
        writer = pq.ParquetWriter(output, schema=schema, compression="GZIP")

        for chunk in pd.read_sql_query(
            dataset.query,
            conn,
            chunksize=chunksize,
            dtype_backend=settings.DEFAULT_DTYPE_BACKEND,
            index_col=dataset.indexes,
        ):
            writer.write_batch(
                pa.RecordBatch.from_pandas(chunk, schema=schema, preserve_index=True)
            )
            yield get_batch(output)
            output.seek(0)

    writer.close()
    # When closing file, the parquet writer adds required footer and magic bytes. We
    # need those so that the Parqet file is readable.
    yield get_batch(output)
    output.close()


def sql2csv(dataset: Dataset, chunksize: int = 5000) -> Generator[str, None, None]:
    """Stream SQL rows to CSV."""
    with engine.connect() as conn:
        for c, chunk in enumerate(
            pd.read_sql_query(dataset.query, conn, chunksize=chunksize)
        ):
            yield chunk.to_csv(header=True if c == 0 else False, index=False)


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

    streamer: Optional[Callable[[Dataset, int], Generator]] = None
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
        streamer(dataset, chunksize=settings.CHUNK_SIZE),
        media_type=media_type,
    )


# Database
logger.debug(f"{settings.DATABASE_URL=}")
engine = create_engine(settings.DATABASE_URL)

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
    app.state.datasets = populate_datasets()

    if settings.SENTRY_DSN is not None:
        sentry_sdk.init(
            dsn=str(settings.SENTRY_DSN),
            enable_tracing=True,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
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
