"""Tests configuration."""

import pytest
from sqlalchemy import create_engine
from typer.testing import CliRunner

from data7.config import settings


@pytest.fixture(scope="session", autouse=True)
def set_test_settings():
    """Force testing environment for settings."""
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")


@pytest.fixture
def db_engine():
    """Get database engine."""
    yield create_engine(settings.DATABASE_URL)


@pytest.fixture
def anyio_backend():
    """Default backend for async tests is set to asyncio.

    Project dependencies are not compatible with trio, hence we choose to restrict
    compatibility tests using the asyncio backend.
    """
    return "asyncio"


@pytest.fixture
def runner():
    """CLI runner."""
    yield CliRunner()
