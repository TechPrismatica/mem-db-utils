"""Tests for async MemDBConnector class."""

from unittest.mock import AsyncMock, patch
from urllib.parse import urlparse

import pytest

from mem_db_utils.asyncio import MemDBConnector as AsyncMemDBConnector
from mem_db_utils.config import DBConfig, DBType


class TestAsyncMemDBConnector:
    """Test the AsyncMemDBConnector class."""

    def test_init_with_defaults(self):
        """Test initialization with default values from .env file."""
        connector = AsyncMemDBConnector()
        assert connector.uri == DBConfig.db_url
        assert connector.db_type == DBConfig.db_type

        # For Redis databases
        if connector.db_type == DBType.REDIS:
            assert connector.connection_type == DBConfig.redis_connection_type
            assert connector.service == DBConfig.redis_master_service
        else:
            # For non-Redis databases, these should be None
            assert connector.connection_type is None
            assert connector.service is None

    def test_init_with_redis_type_override(self):
        """Test initialization with Redis connection type override."""
        connector = AsyncMemDBConnector(redis_type="sentinel")
        assert connector.uri == DBConfig.db_url
        assert connector.db_type == DBConfig.db_type

        if connector.db_type == DBType.REDIS:
            assert connector.connection_type == "sentinel"
            assert connector.service == DBConfig.redis_master_service

    def test_init_with_master_service_override(self):
        """Test initialization with master service override."""
        connector = AsyncMemDBConnector(master_service="custom_master")
        assert connector.uri == DBConfig.db_url
        assert connector.db_type == DBConfig.db_type

        if connector.db_type == DBType.REDIS:
            assert connector.connection_type == DBConfig.redis_connection_type
            assert connector.service == "custom_master"

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    async def test_connect_direct_connection(self, mock_from_url):
        """Test direct async database connection."""
        mock_connection = AsyncMock()

        # Mock from_url to return a coroutine
        async def mock_coro():
            return mock_connection

        mock_from_url.return_value = mock_coro()

        connector = AsyncMemDBConnector()
        # Only test direct connection if not using sentinel
        if connector.connection_type != "sentinel":
            result = await connector.connect(db=1)

            mock_from_url.assert_called_once_with(url=DBConfig.db_url, db=1, decode_responses=True)
            assert result == mock_connection

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    async def test_connect_with_custom_kwargs(self, mock_from_url):
        """Test async connection with custom keyword arguments."""
        mock_connection = AsyncMock()

        # Mock from_url to return a coroutine
        async def mock_coro():
            return mock_connection

        mock_from_url.return_value = mock_coro()

        connector = AsyncMemDBConnector()
        if connector.connection_type != "sentinel":
            result = await connector.connect(db=2, decode_response=False)

            mock_from_url.assert_called_once_with(url=DBConfig.db_url, db=2, decode_responses=False)
            assert result == mock_connection

    @pytest.mark.asyncio
    @patch("redis.asyncio.Sentinel")
    async def test_connect_sentinel(self, mock_sentinel_class):
        """Test async Redis Sentinel connection when configured."""
        mock_sentinel = AsyncMock()
        mock_master = AsyncMock()
        mock_master.select = AsyncMock()
        mock_sentinel.master_for.return_value = mock_master
        mock_sentinel_class.return_value = mock_sentinel

        connector = AsyncMemDBConnector()
        if connector.connection_type == "sentinel" and connector.db_type == DBType.REDIS:
            result = await connector.connect(db=3)

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

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    async def test_connect_default_db(self, mock_from_url):
        """Test async connection with default database (0)."""
        mock_connection = AsyncMock()

        # Mock from_url to return a coroutine
        async def mock_coro():
            return mock_connection

        mock_from_url.return_value = mock_coro()

        connector = AsyncMemDBConnector()
        if connector.connection_type != "sentinel":
            result = await connector.connect()  # No db parameter

            mock_from_url.assert_called_once_with(
                url=DBConfig.db_url,
                db=0,  # Default value
                decode_responses=True,
            )
            assert result == mock_connection

    def test_slots_attribute(self):
        """Test that the class uses __slots__ for memory efficiency."""
        connector = AsyncMemDBConnector()

        # Check that __slots__ is defined
        assert hasattr(AsyncMemDBConnector, "__slots__")
        expected_slots = ("uri", "db_type", "connection_type", "service")
        assert AsyncMemDBConnector.__slots__ == expected_slots

        # Verify we can't add arbitrary attributes
        with pytest.raises(AttributeError):
            connector.new_attribute = "test"

    def test_non_redis_db_type_behavior(self):
        """Test async connector behavior with non-Redis database types."""
        connector = AsyncMemDBConnector()
        if connector.db_type != DBType.REDIS:
            # For non-Redis databases, connection_type and service should be None
            assert connector.connection_type is None
            assert connector.service is None

    @pytest.mark.asyncio
    async def test_error_handling_in_connect(self):
        """Test error handling in async connect method."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Connection failed")

            connector = AsyncMemDBConnector()
            if connector.connection_type != "sentinel":
                with pytest.raises(Exception, match="Connection failed"):
                    await connector.connect()

    @pytest.mark.asyncio
    async def test_error_handling_in_sentinel(self):
        """Test error handling in async sentinel method."""
        with patch("redis.asyncio.Sentinel") as mock_sentinel_class:
            mock_sentinel_class.side_effect = Exception("Sentinel connection failed")

            connector = AsyncMemDBConnector(redis_type="sentinel")
            if connector.db_type == DBType.REDIS:
                with pytest.raises(Exception, match="Sentinel connection failed"):
                    await connector.connect()
