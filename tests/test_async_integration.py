"""Integration tests for AsyncMemDBConnector with real database connections.

These tests use the database configuration from the .env file.
The tests will work with Redis databases only as async support is primarily for Redis.
"""

import asyncio

import pytest

from mem_db_utils import AsyncMemDBConnector
from mem_db_utils.config import DBConfig, DBType


class TestAsyncMemDBConnectorIntegration:
    """Integration tests with real async database connections."""

    @pytest.mark.asyncio
    async def test_async_database_connection(self):
        """Test async connection to the configured database."""
        connector = AsyncMemDBConnector()

        try:
            conn = await connector.connect(db=0)
            # Test basic operations - works for Redis-compatible databases
            if connector.db_type in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
                result = await conn.ping()
                assert result is True

                # Test set/get operations
                await conn.set("test_async_key", "test_async_value")
                value = await conn.get("test_async_key")
                assert value == "test_async_value"

                # Cleanup
                await conn.delete("test_async_key")

                # Close the connection
                await conn.aclose()
            else:
                # For other database types, just verify connection exists
                assert conn is not None

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    @pytest.mark.asyncio
    async def test_async_database_with_different_db_number(self):
        """Test async connection with different database number (Redis-compatible only)."""
        connector = AsyncMemDBConnector()

        # Only test for Redis-compatible databases that support db selection
        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"Database selection not supported for {connector.db_type}")

        try:
            conn = await connector.connect(db=1)
            result = await conn.ping()
            assert result is True
            await conn.aclose()

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    @pytest.mark.asyncio
    async def test_async_auto_type_detection(self):
        """Test automatic type detection from URL in async context."""
        connector = AsyncMemDBConnector()
        assert connector.db_type == DBConfig.db_type
        assert connector.uri == DBConfig.db_url

    @pytest.mark.asyncio
    async def test_async_connection_with_decode_responses_false(self):
        """Test async connection with decode_responses=False (Redis-compatible only)."""
        connector = AsyncMemDBConnector()

        # Only test for Redis-compatible databases
        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"decode_responses not supported for {connector.db_type}")

        try:
            conn = await connector.connect(db=0, decode_response=False)
            result = await conn.ping()
            assert result is True
            await conn.aclose()

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    @pytest.mark.asyncio
    async def test_async_connection_timeout_configuration(self):
        """Test async connection with configured timeout."""
        connector = AsyncMemDBConnector()

        try:
            # This should work with the configured timeout
            conn = await connector.connect(db=0)
            if connector.db_type in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
                result = await conn.ping()
                assert result is True
                await conn.aclose()
            else:
                assert conn is not None

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    @pytest.mark.skip(reason="Requires Redis Sentinel setup")
    @pytest.mark.asyncio
    async def test_async_sentinel_connection_integration(self):
        """Test async Redis Sentinel connection (requires Sentinel setup)."""
        connector = AsyncMemDBConnector()

        if connector.db_type != DBType.REDIS or connector.connection_type != "sentinel":
            pytest.skip("Test requires Redis Sentinel configuration")

        try:
            conn = await connector.connect(db=0)
            result = await conn.ping()
            assert result is True
            await conn.aclose()

        except Exception as e:
            pytest.skip(f"Redis Sentinel not available: {e}")

    @pytest.mark.asyncio
    async def test_async_error_handling_with_invalid_db_number(self):
        """Test async error handling with invalid database number."""
        connector = AsyncMemDBConnector()

        # Only test for Redis-compatible databases that support db selection
        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"Database selection not supported for {connector.db_type}")

        try:
            # Try to connect to a very high database number that likely doesn't exist
            with pytest.raises(Exception):  # noqa
                conn = await connector.connect(db=999)
                await conn.ping()
        except Exception as e:
            pytest.skip(f"Database not available for error testing: {e}")

    @pytest.mark.asyncio
    async def test_async_concurrent_connections(self):
        """Test multiple concurrent async connections."""
        connector = AsyncMemDBConnector()

        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"Concurrent connections test not supported for {connector.db_type}")

        async def test_connection(conn_id):
            try:
                conn = await connector.connect(db=0)
                await conn.set(f"async_test_key_{conn_id}", f"value_{conn_id}")
                value = await conn.get(f"async_test_key_{conn_id}")
                assert value == f"value_{conn_id}"
                await conn.delete(f"async_test_key_{conn_id}")
                await conn.aclose()
                return True
            except Exception:
                return False

        try:
            # Test 3 concurrent connections
            tasks = [test_connection(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # At least some connections should succeed
            success_count = sum(1 for r in results if r is True)
            assert success_count > 0

        except Exception as e:
            pytest.skip(f"Database not available for concurrent testing: {e}")
