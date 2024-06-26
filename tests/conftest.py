"""Tests configuration."""

import pytest
from data7.config import settings
from typer.testing import CliRunner


@pytest.fixture(scope="session", autouse=True)
def set_test_settings():
    """Force testing environment for settings."""
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")


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
