"""Data7 Command Line Interface."""

import copy
import shutil
import sys
from enum import IntEnum, StrEnum
from pathlib import Path
from sqlite3 import OperationalError as SqliteOperationalError
from typing import Optional

import sqlalchemy
import typer
import uvicorn
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text

import data7
from data7.models import Dataset, Extension
from data7.streamers import sql2csv, sql2parquet
from data7.utils import populate_datasets

cli = typer.Typer(name="data7", no_args_is_help=True, pretty_exceptions_short=True)
console = Console(stderr=True)


class ExitCodes(IntEnum):
    """data7 exit codes."""

    OK = 0
    INCOMPLETE_CONFIGURATION = 1
    INVALID_CONFIGURATION = 2
    INVALID_ARGUMENT = 3


class LogLevels(StrEnum):
    """Allowed log levels for the run command."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@cli.command()
def init():
    """Initialize a data7 project."""
    console.print(
        "[cyan]Creating configuration files from distributed templates...[/cyan]\n"
    )
    # Get data7 distributed settings files
    root_path = Path(data7.__file__).parent
    for settings_file in sorted(root_path.glob("*.yaml.dist")):
        dest = Path(settings_file.stem)
        check = "❌"
        remark = "skipped"
        if not dest.exists():
            shutil.copyfile(settings_file, dest)
            check = "✅"
            remark = ""
        console.print(f" {check} {dest} [yellow]{remark}[/yellow]")

    console.print("\n[cyan]Project ready to be configured 💫[/cyan]")

    console.print(
        "\n👉 Edit the [cyan].secrets.yaml[/cyan] file to set your database URL:\n"
    )
    console.print(
        Syntax(
            """# .secrets.yaml
#
# Example settings for production environment
production:
  DATABASE_URL: "postgresql+psycopg://user:pass@server:port/acme"
    """,
            "yaml",
        )
    )

    console.print(
        "\n👉 Edit the [cyan]data7.yaml[/cyan] file to define your datasets:\n"
    )
    console.print(
        Syntax(
            """# data7.yaml
#
# Example settings for production environment
production:
  datasets:
    - basename: "invoices"
      query: "SELECT * FROM Invoices" \
    """,
            "yaml",
        )
    )

    console.print("\n👉 Test your configuration by running the development server:\n")
    console.print(Syntax("# Type the following command in a terminal\ndata7 run", "sh"))

    console.print("\nIf everything went well, the webserver should start ✨\n")

    console.print(
        (
            "💡 [i]If not, the [not i green]data7 check[/not i green] command should "
            "give you hints about what went wrong.\n"
        )
    )


def check_settings_files_exist():
    """Check if all settings files exist."""
    console.rule("[yellow]check[/yellow] // [bold cyan]settings files exist")

    for setting_file in data7.config.SETTINGS_FILES:
        if not Path(setting_file).exists():
            console.print(f"❌ {setting_file} is missing")
            raise typer.Exit(ExitCodes.INCOMPLETE_CONFIGURATION)
        console.print(f"✅ {setting_file}")


def check_settings_files_format():
    """Check all settings files format as valid, safe YAML."""
    console.rule("[yellow]check[/yellow] // [bold cyan]settings files format")

    for setting_file in data7.config.SETTINGS_FILES:
        try:
            content = yaml.safe_load(Path(setting_file).read_text())
        except yaml.parser.ParserError as err:
            console.print(f"❌ {setting_file}")
            console.print_exception(max_frames=1, suppress=[yaml])
            raise typer.Exit(ExitCodes.INVALID_CONFIGURATION) from err
        console.print(f"✅ {setting_file}")
        console.print(content)


def check_database_connection(engine: Engine):
    """Check database URL connection."""
    console.rule("[yellow]check[/yellow] // [bold cyan]database connection")

    with console.status("Connecting to database...", spinner="dots"):
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    console.print("✅ database connection looks ok from here")
    console.print("⚠️[yellow i] Note that there may be false positive for sqlite")


def check_datasets_queries(engine: Engine):
    """Check datasets defined queries."""
    console.rule("[yellow]check[/yellow] // [bold cyan]datasets queries")

    with engine.connect() as conn:
        for dataset in data7.config.settings.datasets:
            console.print(f"👉 [b cyan]{dataset.basename}")
            console.print(f"   [i]{dataset.query}")
            try:
                conn.execute(text(dataset.query)).scalar()
            except (OperationalError, SqliteOperationalError) as err:
                console.print("❌ Invalid database query")
                console.print_exception(max_frames=1, suppress=[sqlalchemy])
                raise typer.Exit(ExitCodes.INVALID_CONFIGURATION) from err
            console.print("   ✅ valid\n")


@cli.command()
def check():
    """Check data7 project configuration.

    Checks:

    1. all settings files SHOULD exist

    2. settings files format SHOULD be valid YAML

    3. configured database connection SHOUD be valid (driver installed and valid url)

    4. datasets SQL queries SHOULD be valid SQL
    """
    engine = create_engine(data7.config.settings.DATABASE_URL)

    check_settings_files_exist()
    check_settings_files_format()
    check_database_connection(engine)
    check_datasets_queries(engine)

    console.print("\n💫 All checks are successful. w00t 🎉")


@cli.command()
def stream(extension: Extension, name: str):
    """Stream a dataset given its name and a selected extension."""
    datasets = data7.config.settings.datasets
    names = [d.basename for d in datasets]
    if name not in names:
        console.print(f"❌ Dataset '{name}' not found.")
        console.print(f"Allowed values are: {names}")
        raise typer.Exit(ExitCodes.INVALID_ARGUMENT)

    # Create database engine
    engine = create_engine(data7.config.settings.DATABASE_URL)

    # Get dataset
    datasets = populate_datasets(engine)
    dataset: Dataset = next((d for d in datasets if d.basename == name))
    query_md = Markdown(f"🗃️ SQL Query\n```sql\n{dataset.query}\n```\n\n")
    console.print(query_md)

    # Start streaming
    streamer = sql2csv
    stream = sys.stdout
    if extension == Extension.PARQUET:
        streamer = sql2parquet
        stream = sys.stdout.buffer
    for chunk in streamer(engine, dataset, chunksize=data7.config.settings.CHUNK_SIZE):
        stream.write(chunk)


@cli.command()
def run(  # noqa: PLR0913
    host: Optional[str] = None,
    port: Optional[int] = None,
    reload: bool = False,
    workers: Optional[int] = None,
    root_path: str = "",
    proxy_headers: bool = False,
    log_level: LogLevels = LogLevels.INFO,
):
    """Run data7 web server."""
    default_host = "localhost"
    default_port = 8000
    host = data7.config.settings.get("HOST", default_host) if host is None else host
    port = data7.config.settings.get("PORT", default_port) if port is None else port
    # Configure logging
    log_config = copy.copy(uvicorn.config.LOGGING_CONFIG)
    log_config["loggers"]["data7.app"] = {
        "handlers": ["default"],
        "level": log_level.value.upper(),
        "propagate": False,
    }

    uvicorn.run(
        "data7.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        root_path=root_path,
        proxy_headers=proxy_headers,
        log_level=log_level,
        log_config=log_config,
    )


# Get a provisionned Click instance to automatically generate CLI commands documentation
# using the mkdocs-click module
cli_click = typer.main.get_command(cli)
