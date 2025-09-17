"""Test configuration and shared fixtures for mem-db-utils tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection for testing."""
    mock_conn = MagicMock()
    mock_conn.ping.return_value = True
    mock_conn.select.return_value = True
    return mock_conn


@pytest.fixture
def mock_sentinel():
    """Mock Redis Sentinel for testing."""
    mock_sentinel = MagicMock()
    mock_master = MagicMock()
    mock_master.select.return_value = True
    mock_sentinel.master_for.return_value = mock_master
    return mock_sentinel
