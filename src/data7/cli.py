"""Data7 Command Line Interface."""

import copy
import shutil
from enum import IntEnum, StrEnum
from pathlib import Path
from sqlite3 import OperationalError as SqliteOperationalError
from typing import Optional

import anyio
import databases
import typer
import uvicorn
import yaml
from anyio import run as async_run
from rich.console import Console
from rich.syntax import Syntax
from sqlalchemy.exc import OperationalError

import data7

cli = typer.Typer(name="data7", no_args_is_help=True, pretty_exceptions_short=True)
console = Console()


class ExitCodes(IntEnum):
    """data7 exit codes."""

    OK: int = 0
    INCOMPLETE_CONFIGURATION: int = 1
    INVALID_CONFIGURATION: int = 2


class LogLevels(StrEnum):
    """Allowed log levels for the run command."""

    DEBUG: str = "debug"
    INFO: str = "info"
    WARNING: str = "warning"
    ERROR: str = "error"
    CRITICAL: str = "critical"


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
  DATABASE_URL: "postgresql+asyncpg://user:pass@server:port/acme"
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


async def check_database_connection():
    """Check database URL connection."""
    console.rule("[yellow]check[/yellow] // [bold cyan]database connection")

    database_url = data7.config.settings.DATABASE_URL
    with console.status("Connecting to database...", spinner="dots"):
        database = databases.Database(database_url)
        await database.connect()
        await database.execute(query="SELECT 1")
    await database.disconnect()
    console.print("✅ database connection looks ok from here")
    console.print("⚠️[yellow i] Note that there may be false positive for sqlite")


async def check_datasets_queries():
    """Check datasets defined queries."""
    console.rule("[yellow]check[/yellow] // [bold cyan]datasets queries")

    settings = data7.config.settings
    database = databases.Database(settings.DATABASE_URL)
    await database.connect()

    for dataset in settings.datasets:
        console.print(f"👉 [b cyan]{dataset.basename}")
        console.print(f"   [i]{dataset.query}")
        try:
            await database.fetch_one(dataset.query)
        except (OperationalError, SqliteOperationalError) as err:
            console.print("❌ Invalid database query")
            console.print_exception(max_frames=1, suppress=[anyio, databases])
            raise typer.Exit(ExitCodes.INVALID_CONFIGURATION) from err
        console.print("   ✅ valid\n")

    await database.disconnect()


@cli.command()
def check():
    """Check data7 project configuration.

    Checks:

    1. all settings files SHOULD exist

    2. settings files format SHOULD be valid YAML

    3. configured database connection SHOUD be valid (driver installed and valid url)

    4. datasets SQL queries SHOULD be valid SQL
    """
    check_settings_files_exist()
    check_settings_files_format()
    async_run(check_database_connection)
    async_run(check_datasets_queries)

    console.print("\n💫 All checks are successful. w00t 🎉")


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
