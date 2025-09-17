"""Tests for the MemDBConnector class."""

from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from mem_db_utils import MemDBConnector
from mem_db_utils.config import DBConfig, DBType


class TestMemDBConnector:
    """Test the MemDBConnector class."""

    def test_init_with_defaults(self):
        """Test initialization with default values from .env file."""
        connector = MemDBConnector()
        assert connector.uri == DBConfig.db_url
        assert connector.db_type == DBConfig.db_type
        assert connector.connection_type == DBConfig.redis_connection_type
        assert connector.service == DBConfig.redis_master_service

    def test_init_with_redis_type_override(self):
        """Test initialization with Redis connection type override."""
        connector = MemDBConnector(redis_type="sentinel")
        if connector.db_type == DBType.REDIS:
            assert connector.connection_type == "sentinel"
        else:
            assert connector.connection_type is None

    def test_init_with_master_service_override(self):
        """Test initialization with master service override."""
        connector = MemDBConnector(master_service="mymaster")
        if connector.db_type == DBType.REDIS:
            assert connector.service == "mymaster"
        else:
            assert connector.service is None

    @patch("redis.from_url")
    def test_connect_direct_connection(self, mock_from_url):
        """Test direct database connection."""
        mock_connection = MagicMock()
        mock_from_url.return_value = mock_connection

        connector = MemDBConnector()
        # Only test direct connection if not using sentinel
        if connector.connection_type != "sentinel":
            result = connector.connect(db=1)

            mock_from_url.assert_called_once_with(url=DBConfig.db_url, db=1, decode_responses=True)
            assert result == mock_connection

    @patch("redis.from_url")
    def test_connect_with_custom_kwargs(self, mock_from_url):
        """Test connection with custom keyword arguments."""
        mock_connection = MagicMock()
        mock_from_url.return_value = mock_connection

        connector = MemDBConnector()
        if connector.connection_type != "sentinel":
            result = connector.connect(db=2, decode_response=False)

            mock_from_url.assert_called_once_with(url=DBConfig.db_url, db=2, decode_responses=False)
            assert result == mock_connection

    @patch("redis.Sentinel")
    def test_connect_sentinel(self, mock_sentinel_class):
        """Test Redis Sentinel connection when configured."""
        mock_sentinel = MagicMock()
        mock_master = MagicMock()
        mock_sentinel.master_for.return_value = mock_master
        mock_sentinel_class.return_value = mock_sentinel

        connector = MemDBConnector()
        if connector.connection_type == "sentinel" and connector.db_type == DBType.REDIS:
            result = connector.connect(db=3)

            # Verify Sentinel was created with correct parameters
            parsed_uri = urlparse(DBConfig.db_url)
            expected_hosts = [(parsed_uri.hostname, parsed_uri.port)]

            mock_sentinel_class.assert_called_once_with(
                expected_hosts, socket_timeout=DBConfig.db_timeout, password=parsed_uri.password
            )

            # Verify master connection was requested
            mock_sentinel.master_for.assert_called_once_with(DBConfig.redis_master_service, decode_responses=True)

            # Verify database selection
            mock_master.select.assert_called_once_with(3)
            assert result == mock_master

    @patch("redis.from_url")
    def test_connect_default_db(self, mock_from_url):
        """Test connection with default database (0)."""
        mock_connection = MagicMock()
        mock_from_url.return_value = mock_connection

        connector = MemDBConnector()
        if connector.connection_type != "sentinel":
            result = connector.connect()  # No db parameter

            mock_from_url.assert_called_once_with(
                url=DBConfig.db_url,
                db=0,  # Default value
                decode_responses=True,
            )
            assert result == mock_connection

    def test_slots_attribute(self):
        """Test that the class uses __slots__ for memory efficiency."""
        connector = MemDBConnector()

        # Check that __slots__ is defined
        assert hasattr(MemDBConnector, "__slots__")
        expected_slots = ("uri", "db_type", "connection_type", "service")
        assert MemDBConnector.__slots__ == expected_slots

        # Verify we can't add arbitrary attributes
        with pytest.raises(AttributeError):
            connector.new_attribute = "test"

    def test_non_redis_db_type_behavior(self):
        """Test connector behavior with non-Redis database types."""
        connector = MemDBConnector()
        if connector.db_type != DBType.REDIS:
            # For non-Redis databases, connection_type and service should be None
            assert connector.connection_type is None
            assert connector.service is None
