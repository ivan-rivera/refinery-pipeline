"""Shared pytest fixtures."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()
