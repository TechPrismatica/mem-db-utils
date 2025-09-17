from enum import StrEnum
from typing import Optional

from pydantic import ConfigDict, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class DBType(StrEnum):
    REDIS = "redis"
    MEMCACHED = "memcached"
    DRAGONFLY = "dragonfly"
    VALKEY = "valkey"


class _DBConfig(BaseSettings):
    db_url: str
    db_type: Optional[DBType] = None
    redis_connection_type: Optional[str] = None
    redis_master_service: Optional[str] = None
    db_timeout: Optional[int] = 30

    model_config = ConfigDict(
        populate_by_name=True,
    )

    @field_validator("db_type")
    def validate_db_type(cls, value: Optional[DBType], info: ValidationInfo) -> Optional[DBType]:
        if value is None:
            conn_protocol = info.data.get("db_url", "").split("://")[0]
            match conn_protocol:
                case "redis":
                    return DBType.REDIS
                case "memcached":
                    return DBType.MEMCACHED
                case "dragonfly":
                    return DBType.DRAGONFLY
                case "valkey":
                    return DBType.VALKEY
                case _:
                    raise ValueError(f"Unsupported connection protocol: {conn_protocol}")
        return value


# This should not be modified. The env variables are loaded from .env files or system environment.
# No Lazy loading is used here to ensure the config is always available.
DBConfig = _DBConfig()

__all__ = ["DBType", "DBConfig"]
