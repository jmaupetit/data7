"""Data7 CLI tests."""

import sqlite3
from pathlib import Path

import pytest

import data7
from data7.cli import ExitCodes, cli


def test_command_help(runner):
    """Test the `data7 --help` command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == ExitCodes.OK


def test_init_command(runner):
    """Test the `data7 init` command."""
    with runner.isolated_filesystem():
        for setting_file in data7.config.SETTINGS_FILES:
            assert Path(setting_file).exists() is False

        result = runner.invoke(cli, ["init"])
        assert result.exit_code == ExitCodes.OK

        # All settings files should exist now
        for setting_file in data7.config.SETTINGS_FILES:
            assert Path(setting_file).exists() is True


def test_check_command(runner):
    """Test the `data7 check` command."""
    # Everything should be ok for the configured test environment
    result = runner.invoke(cli, ["check"])
    assert result.exit_code == ExitCodes.OK


def test_check_command_with_missing_configuration_file(runner):
    """Test the `data7 check` command when a configuration file is missing."""
    # Configuration files are missing
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == ExitCodes.INCOMPLETE_CONFIGURATION

        # One configuration file will be missing
        for setting_file in data7.config.SETTINGS_FILES[:-1]:
            Path(setting_file).touch()
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == ExitCodes.INCOMPLETE_CONFIGURATION


def test_check_command_with_invalid_configuration_file(runner):
    """Test the `data7 check` command when a configuration file is invalid."""
    # A configuration file is invalid
    with runner.isolated_filesystem():
        for setting_file in data7.config.SETTINGS_FILES:
            Path(setting_file).touch()
        Path(data7.config.SETTINGS_FILES[0]).write_text(
            """
development:
  foo: 'bar'
 indentation_matter:
            """
        )
        result = runner.invoke(cli, ["check"])
        assert result.exit_code == ExitCodes.INVALID_CONFIGURATION


def test_check_command_with_invalid_database_url(runner):
    """Test the `data7 check` command whith an invalid database url."""
    with runner.isolated_filesystem():
        for setting_file in data7.config.SETTINGS_FILES:
            Path(setting_file).touch()
        Path(".secrets.yaml").write_text(
            """
development:
  DATABASE_URL: "postgresql://foo:bar@localhost:5432/lol"
            """
        )
        result = runner.invoke(
            cli,
            args=["check"],
        )
        assert result.exit_code != ExitCodes.OK


def test_check_command_with_invalid_dataset_query(runner):
    """Test the `data7 check` command whith an invalid dataset query."""
    with runner.isolated_filesystem():
        # Set default configuration
        result = runner.invoke(cli, ["init"])

        # Override datasets definition
        data7_configuration = Path("data7.yaml")
        data7_configuration.write_text(
            """
testing:
  datasets:
    - basename: places
      query: "SELECT * FROM Places"
            """
        )

        # Create database
        db_path = Path("db/tests.db")
        db_path.parent.mkdir()
        connection = sqlite3.connect(db_path)
        connection.close()

        result = runner.invoke(
            cli,
            args=["check"],
            catch_exceptions=False,
        )
        assert result.exit_code == ExitCodes.INVALID_CONFIGURATION


@pytest.mark.parametrize("extension", ("csv", "parquet"))
def test_stream_command_with_invalid_dataset(runner, extension):
    """Test the `data7 stream [extension]` command with an invalid dataset."""
    result = runner.invoke(cli, ["stream", extension, "foo"])
    assert result.exit_code == ExitCodes.INVALID_ARGUMENT
    assert "Dataset 'foo' not found." in result.output


@pytest.mark.parametrize(
    "extension,dataset",
    (
        ("csv", "employees"),
        ("parquet", "customers"),
        ("csv", "employees"),
        ("parquet", "customers"),
    ),
)
def test_stream_command(runner, extension, dataset):
    """Test the `data7 stream [extension]` command with an invalid dataset."""
    result = runner.invoke(cli, ["stream", extension, dataset])
    assert result.exit_code == ExitCodes.OK
