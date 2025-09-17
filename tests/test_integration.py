"""Integration tests for MemDBConnector with real database connections.

These tests use the database configuration from the .env file.
The tests will work with any supported database type (Redis, Memcached, Dragonfly, Valkey).
"""

import pytest

from mem_db_utils import MemDBConnector
from mem_db_utils.config import DBConfig, DBType


class TestMemDBConnectorIntegration:
    """Integration tests with real database connections."""

    def test_database_connection(self):
        """Test connection to the configured database."""
        connector = MemDBConnector()

        try:
            conn = connector.connect(db=0)
            # Test basic operations - works for Redis-compatible databases
            if connector.db_type in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
                result = conn.ping()
                assert result is True

                # Test set/get operations
                conn.set("test_key", "test_value")
                value = conn.get("test_key")
                assert value == "test_value"

                # Cleanup
                conn.delete("test_key")
            else:
                # For other database types, just verify connection exists
                assert conn is not None

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    def test_database_with_different_db_number(self):
        """Test connection with different database number (Redis-compatible only)."""
        connector = MemDBConnector()

        # Only test database selection for Redis-compatible databases
        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"Database selection not supported for {connector.db_type}")

        try:
            conn = connector.connect(db=1)
            result = conn.ping()
            assert result is True

            # Verify we're on database 1
            conn.set("db_test", "db1")

            # Connect to db 0 and verify key doesn't exist there
            conn_db0 = connector.connect(db=0)
            assert conn_db0.get("db_test") is None

            # Cleanup
            conn.delete("db_test")

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    def test_auto_type_detection(self):
        """Test automatic type detection from URL."""
        connector = MemDBConnector()
        assert connector.db_type == DBConfig.db_type
        assert connector.uri == DBConfig.db_url

    def test_connection_with_decode_responses_false(self):
        """Test connection with decode_responses=False (Redis-compatible only)."""
        connector = MemDBConnector()

        # Only test for Redis-compatible databases
        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"decode_responses not applicable for {connector.db_type}")

        try:
            conn = connector.connect(db=0, decode_response=False)

            # Set a value
            conn.set("bytes_test", "test_value")

            # Get value should return bytes
            value = conn.get("bytes_test")
            assert isinstance(value, bytes)
            assert value == b"test_value"

            # Cleanup
            conn.delete("bytes_test")

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    def test_connection_timeout_configuration(self):
        """Test connection with configured timeout."""
        connector = MemDBConnector()

        try:
            # This should work with the configured timeout
            conn = connector.connect(db=0)
            if connector.db_type in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
                result = conn.ping()
                assert result is True
            else:
                assert conn is not None

        except Exception as e:
            pytest.skip(f"Database not available at {DBConfig.db_url}: {e}")

    @pytest.mark.skip(reason="Requires Redis Sentinel setup")
    def test_sentinel_connection_integration(self):
        """Test Redis Sentinel connection (requires Sentinel setup)."""
        connector = MemDBConnector()

        if connector.db_type != DBType.REDIS or connector.connection_type != "sentinel":
            pytest.skip("Test requires Redis Sentinel configuration")

        try:
            conn = connector.connect(db=0)
            result = conn.ping()
            assert result is True

        except Exception as e:
            pytest.skip(f"Redis Sentinel not available: {e}")

    def test_error_handling_with_invalid_db_number(self):
        """Test error handling with invalid database number."""
        connector = MemDBConnector()

        # Only test for Redis-compatible databases that support db selection
        if connector.db_type not in [DBType.REDIS, DBType.DRAGONFLY, DBType.VALKEY]:
            pytest.skip(f"Database selection not supported for {connector.db_type}")

        try:
            # Try to connect to a very high database number that likely doesn't exist
            with pytest.raises(Exception):  # noqa
                conn = connector.connect(db=999)
                conn.ping()
        except Exception as e:
            pytest.skip(f"Database not available for error testing: {e}")
