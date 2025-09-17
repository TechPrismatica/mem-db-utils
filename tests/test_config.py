"""Tests for the config module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from mem_db_utils.config import DBType, _DBConfig


class TestDBType:
    """Test the DBType enum."""

    def test_db_type_values(self):
        """Test that DBType has correct values."""
        assert DBType.REDIS == "redis"
        assert DBType.MEMCACHED == "memcached"
        assert DBType.DRAGONFLY == "dragonfly"
        assert DBType.VALKEY == "valkey"

    def test_db_type_enum_members(self):
        """Test that all expected enum members exist."""
        expected_types = {"redis", "memcached", "dragonfly", "valkey"}
        actual_types = {db_type.value for db_type in DBType}
        assert actual_types == expected_types


class TestDBConfig:
    """Test the DBConfig class."""

    def test_config_with_explicit_db_type(self):
        """Test configuration with explicitly set db_type."""
        with patch.dict(os.environ, {"DB_URL": "redis://localhost:6379/0", "DB_TYPE": "redis"}):
            config = _DBConfig()
            assert config.db_url == "redis://localhost:6379/0"
            assert config.db_type == DBType.REDIS
            assert config.db_timeout == 30

    def test_config_auto_detect_from_url(self, monkeypatch):
        """Test automatic detection of database type from URL."""
        test_cases = [
            ("redis://localhost:6379/0", DBType.REDIS),
            ("memcached://localhost:11211", DBType.MEMCACHED),
            ("dragonfly://localhost:6380", DBType.DRAGONFLY),
            ("valkey://localhost:6381", DBType.VALKEY),
        ]

        for url, expected_type in test_cases:
            config = _DBConfig(db_url=url, db_type=None)
            assert config.db_type == expected_type

    def test_config_unsupported_protocol(self):
        """Test that unsupported protocols raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _DBConfig(db_url="mysql://localhost:3306", db_type=None)

            # Check that the error message mentions unsupported protocol
            error_msg = str(exc_info.value)
            assert "Unsupported connection protocol" in error_msg

    def test_config_optional_settings(self):
        """Test optional configuration settings."""
        with patch.dict(
            os.environ,
            {
                "DB_URL": "redis://localhost:6379/0",
                "REDIS_CONNECTION_TYPE": "sentinel",
                "REDIS_MASTER_SERVICE": "mymaster",
                "DB_TIMEOUT": "60",
            },
        ):
            config = _DBConfig()
            assert config.redis_connection_type == "sentinel"
            assert config.redis_master_service == "mymaster"
            assert config.db_timeout == 60

    def test_config_defaults(self):
        """Test default values."""
        with patch.dict(os.environ, {"DB_URL": "redis://localhost:6379/0"}):
            config = _DBConfig()
            assert config.redis_connection_type is None
            assert config.redis_master_service is None
            assert config.db_timeout == 30

    def test_config_missing_db_url(self):
        """Test that missing DB_URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _DBConfig(db_url=None, db_type="redis")

        # Check that the error is about missing db_url
        error_msg = str(exc_info.value)
        assert "db_url" in error_msg.lower()

    def test_config_override_auto_detection(self):
        """Test that explicit db_type overrides auto-detection."""
        with patch.dict(os.environ, {"DB_URL": "redis://localhost:6379/0", "DB_TYPE": "valkey"}):
            config = _DBConfig()
            assert config.db_type == DBType.VALKEY  # Overridden value
