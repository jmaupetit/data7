"""Data7 implementation benchmark.

Our main intention here is to compare data7 initial implementation using
the CSV native library against Pandas.

You can run this script with the following command:

uv run python scripts/benchmark.py

For performance testing, we use the imdb-sql project to seed the database:
https://github.com/jmaupetit/imdb-sql

"""

import asyncio
import csv
from io import StringIO
from typing import Any, AsyncGenerator

import databases
from pyinstrument import Profiler
from rich.console import Console
from rich.live import Live
from rich.pretty import Pretty, pprint
from rich.table import Table
from sqlalchemy import create_engine

from data7.app import Dataset
from data7.app import sql2csv as pd_sql2csv
from data7.config import settings

# Databases
database = databases.Database("postgresql+asyncpg://imdb:pass@localhost:5432/imdb")
engine = create_engine("postgresql://imdb:pass@localhost:5432/imdb")

# Profiling
aprofiler = Profiler(interval=settings.profiler_interval, async_mode="enabled")
profiler = Profiler(interval=settings.profiler_interval, async_mode="disabled")

# Display
console = Console()


title_fields = [
    "tconst",
    "titleType",
    "primaryTitle",
    "originalTitle",
    "isAdult",
    "startYear",
    "endYear",
    "runtimeMinutes",
    "genres",
]


# Legacy
async def sql2csv(dataset: Dataset) -> AsyncGenerator[str, Any]:
    """Stream SQL rows to CSV."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=title_fields)

    # Header
    writer.writeheader()
    output.seek(0)
    yield output.readline()

    # Rows
    async for record in database.iterate(dataset.query):
        output.seek(0)
        writer.writerow(dict(zip(record.keys(), record.values(), strict=True)))
        output.seek(0)
        yield output.readline()


# Wrappers
async def _sql2csv(dataset: Dataset) -> float:
    """sql2csv wrapper to handle database connection."""
    await database.connect()
    aprofiler.reset()
    aprofiler.start()
    async for _ in sql2csv(dataset):
        pass
    aprofiler.stop()
    await database.disconnect()
    return aprofiler.last_session.duration if aprofiler.last_session else 0.0


def _pd_sql2csv(dataset: Dataset, chunksize: int = 5000) -> float:
    """sql2any wrapper to handled database connection."""
    profiler.reset()
    profiler.start()
    for _ in pd_sql2csv(engine, dataset, chunksize):
        pass
    profiler.stop()
    return profiler.last_session.duration if profiler.last_session else 0.0


# Output
def render_float(value):
    """Pretty print a float."""
    return pprint(value)


table = Table(title="Data7 implementations Benchmark (Duration for CSV)")
table.add_column("# rows")
table.add_column("v0.5.0", justify="right")
table.add_column("🐼 (1000)", justify="right")
table.add_column("Ratio (1000)", justify="right")
table.add_column("🐼 (5000)", justify="right")
table.add_column("Ratio (5000)", justify="right")
table.add_column("🐼 (10000)", justify="right")
table.add_column("Ratio (10000)", justify="right")

# ruff: noqa: S608
datasets = [
    Dataset(
        basename=f"{rows}",
        query=f'SELECT * FROM "title.basics" LIMIT {rows}',
    )
    for rows in (500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000)
]

with Live(table, refresh_per_second=4):
    for dataset in datasets:
        # Legacy
        legacy = asyncio.run(_sql2csv(dataset))

        # Pandas
        pandas = []
        ratios = []
        for chunksize in (1000, 5000, 10000):
            p = _pd_sql2csv(dataset, chunksize)
            pandas.append(p)
            ratios.append(legacy / p)
        values = (v for couple in zip(pandas, ratios, strict=True) for v in couple)

        table.add_row(
            dataset.basename,
            Pretty(round(legacy, 3)),
            *(Pretty(round(v, 3)) for v in values),
        )

engine.dispose()
