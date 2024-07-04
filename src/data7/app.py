"""Data7 application module."""

import contextlib
import csv
import importlib.metadata
import logging
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import PurePath
from typing import Any, AsyncGenerator, Callable, List, Optional, Tuple

import databases
import pyarrow as pa
import sentry_sdk
from pyarrow import parquet as pq
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.routing import Route
from starlette.status import HTTP_501_NOT_IMPLEMENTED

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class Dataset:
    """Dataset model."""

    basename: str
    query: str
    # Following fields are set dynamically
    fields: Optional[List[str]] = None


class Extension(StrEnum):
    """Supported formats extensions."""

    CSV = "csv"
    PARQUET = "parquet"


class MimeType(StrEnum):
    """MimeTypes for supported formats."""

    CSV = "text/csv"
    PARQUET = "application/vnd.apache.parquet"


async def populate_datasets() -> List[Dataset]:
    """Validate configured datasets and get sql query expected field names."""
    logging.debug("Will populate datasets given configuration...")
    datasets = []

    for raw_dataset in settings.datasets:
        dataset = Dataset(**raw_dataset)

        # Validate database query and get expected field names
        try:
            row = await database.fetch_one(dataset.query)
        # Exception is a bit vague, but there is no high-level exception in databases,
        # i.e. backend-independent exception.
        except Exception as exc:
            raise ValueError(
                f"Dataset '{dataset.basename}' query failed, maybe SQL is invalid"
            ) from exc
        # Query returns no result, we cannot set fields.
        if row is None:
            logger.warning(
                "'%s' query returned no result, dataset will be ignored",
                dataset.basename,
            )
            continue
        # Set fields from database query result
        dataset.fields = list(row._mapping.keys())

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


async def sql2csv(dataset: Dataset) -> AsyncGenerator[str, Any]:
    """Stream SQL rows to CSV."""
    logger.debug("SQL query: %s", dataset.query)

    output = StringIO()

    if dataset.fields is None:
        raise ValueError(
            f"Requested dataset '{dataset.basename}' has no defined fields"
        )

    writer = csv.DictWriter(output, fieldnames=dataset.fields)

    # Header
    writer.writeheader()
    output.seek(0)
    yield output.readline()

    # Rows
    async for record in database.iterate(dataset.query):
        output.seek(0)
        writer.writerow(dict(zip(record.keys(), record.values())))
        output.seek(0)
        yield output.readline()


async def sql2parquet(dataset: Dataset) -> AsyncGenerator[bytes, Any]:
    """Stream SQL rows to parquet."""
    logger.debug("SQL query: %s", dataset.query)

    # Get schema from a subset of data
    records = await database.fetch_all(f"{dataset.query} LIMIT 10")

    def records2batch(records):
        rows = [list(row._mapping) for row in records]
        transposed = list(zip(*rows))
        data = [pa.array(column) for column in transposed]
        return pa.record_batch(data, names=dataset.fields)

    sample = records2batch(records)

    sink = pa.BufferOutputStream()
    writer = pq.ParquetWriter(sink, schema=sample.schema, compression="GZIP")

    # Rows
    batch_records = []
    async for record in database.iterate(dataset.query):
        batch_records.append(record)
        if len(batch_records) < settings.PARQUET_BATCH_SIZE:
            continue
        # Prepare batch
        batch = records2batch(batch_records)
        writer.write_batch(batch)
        batch_records = []

    if len(batch_records):
        batch = records2batch(batch_records)
        writer.write_batch(batch)
    writer.close()

    yield bytes(sink.getvalue())


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

    streamer: Optional[Callable[[Dataset], AsyncGenerator]] = None
    if extension == Extension.CSV:
        streamer = sql2csv
    elif extension == Extension.PARQUET:
        streamer = sql2parquet
    if streamer is None:
        raise HTTPException(
            status_code=HTTP_501_NOT_IMPLEMENTED,
            detail=f"Streamer for extension '{extension}' does not exist",
        )

    return StreamingResponse(streamer(dataset), media_type=media_type)


# Database
database = databases.Database(settings.DATABASE_URL)
logger.debug(f"{settings.DATABASE_URL=}")

# Routes
routes = get_routes_from_datasets(settings.datasets)
logger.debug("Registered routes:\n%s", "\n".join([route.path for route in routes]))


# App
@contextlib.asynccontextmanager
async def lifespan(app):
    """Application lifespan."""
    await database.connect()
    app.state.datasets = await populate_datasets()

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
    await database.disconnect()


middleware = [Middleware(GZipMiddleware, minimum_size=1000)]

logger.info("Active extensions: %s", ", ".join(e for e in Extension))

app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
    debug=settings.DEBUG,
)
