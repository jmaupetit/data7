"""Data7 streamers module."""

import logging
from io import BytesIO
from typing import Generator

import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq
from sqlalchemy import Engine

from .config import settings
from .models import Dataset

logger = logging.getLogger(__name__)


def sql2parquet(engine: Engine, dataset: Dataset, chunksize: int = 5000) -> Generator:
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


def sql2csv(
    engine: Engine, dataset: Dataset, chunksize: int = 5000
) -> Generator[str, None, None]:
    """Stream SQL rows to CSV."""
    with engine.connect() as conn:
        for c, chunk in enumerate(
            pd.read_sql_query(dataset.query, conn, chunksize=chunksize)
        ):
            yield chunk.to_csv(header=True if c == 0 else False, index=False)
