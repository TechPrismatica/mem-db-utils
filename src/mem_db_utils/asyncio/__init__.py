from urllib.parse import urlparse

import redis.asyncio as aioredis

from mem_db_utils.config import DBConfig, DBType


class MemDBConnector:
    __slots__ = ("uri", "db_type", "connection_type", "service")

    def __init__(self, redis_type: str = None, master_service: str = None):
        self.uri = DBConfig.db_url
        self.db_type = DBConfig.db_type
        self.service = None
        self.connection_type = None
        if self.db_type == DBType.REDIS:
            self.connection_type = redis_type or DBConfig.redis_connection_type
            self.service = master_service or DBConfig.redis_master_service

    async def connect(self, db: int = 0, **kwargs):
        """
        The async connect function is used to connect to a MemDB instance asynchronously.

        :param self: Represent the instance of the class
        :param db: int: Specify the database number to connect to
        :return: An async connection object
        """
        if self.connection_type == "sentinel":
            return await self._sentinel(db=db, **kwargs)
        return await aioredis.from_url(url=self.uri, db=db, decode_responses=kwargs.get("decode_response", True))

    async def _sentinel(self, db: int, **kwargs):
        """
        The async _sentinel function is used to connect to a Redis Sentinel service asynchronously.

        :param self: Bind the method to an instance of the class
        :param db: int: Select the database to connect to
        :return: An async connection object
        """
        parsed_uri = urlparse(self.uri)
        sentinel_host = parsed_uri.hostname
        sentinel_port = parsed_uri.port
        redis_password = parsed_uri.password
        sentinel_hosts = [(sentinel_host, sentinel_port)]

        sentinel = aioredis.Sentinel(
            sentinel_hosts,
            socket_timeout=kwargs.get("timeout", DBConfig.db_timeout),
            password=redis_password,
        )

        # Connect to the Redis Sentinel master service and select the specified database
        connection_object = sentinel.master_for(self.service, decode_responses=kwargs.get("decode_response", True))
        await connection_object.select(db)
        return connection_object


__all__ = ["MemDBConnector"]