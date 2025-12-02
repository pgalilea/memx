import redis
from redis.commands.json.path import Path

from memx.engine import BaseEngine
from memx.memory.redis import RedisMemory
from memx.models import RedisEngineConfig
from memx.utils import filter_kwargs


class RedisEngine(BaseEngine):
    key_prefix = "memx:session:"
    array_path = ".messages"

    def __init__(self, uri: str, start_up: bool = False, **kwargs):
        sync_kwargs = filter_kwargs(redis.Redis.__init__, kwargs) | {"decode_responses": True}
        async_kwargs = filter_kwargs(redis.asyncio.Redis.__init__, kwargs) | {  # type: ignore
            "decode_responses": True
        }

        self.sync_client = redis.Redis.from_url(uri, **sync_kwargs)
        self.async_client = redis.asyncio.Redis.from_url(uri, **async_kwargs)  # type: ignore

        self.engine_config = RedisEngineConfig(
            prefix=self.key_prefix,
            array_path=self.array_path,
        )

        self.sync = _sync(self)

        if start_up:
            self.start_up()  # blocking operation

    def create_session(self) -> RedisMemory:
        engine_config = RedisEngineConfig(
            prefix=self.key_prefix,
            array_path=self.array_path,
        )
        return RedisMemory(self.async_client, self.sync_client, engine_config)

    async def get_session(self, id: str) -> RedisMemory | None:
        if (await self.async_client.exists(f"{self.key_prefix}{id}")) > 0:
            return RedisMemory(self.async_client, self.sync_client, self.engine_config, id)

    def start_up(self):
        """Check if the Redis instance is available and if RedisJSON is installed."""

        # self.sync_client.ping()
        # self.sync_client.info()
        try:
            # NOTE: Starting with Redis 8, the JSON data structure is integral to Redis.
            # https://github.com/RedisJSON/RedisJSON
            self.sync_client.get("memx")
            self.sync_client.json().get("memx", Path.root_path())
        except redis.exceptions.ConnectionError as e:  # type: ignore
            raise RuntimeError(f"Failed to connect to Redis instance: {e}") from e
        except Exception as e:
            raise RuntimeError("RedisJSON not found") from e


class _sync:
    """Sync methods for RedisEngine."""

    def __init__(self, parent: "RedisEngine"):
        self.pe = parent

    def get_session(self, id: str) -> RedisMemory | None:
        if self.pe.sync_client.exists(f"{self.pe.key_prefix}{id}") > 0:  # type: ignore
            return RedisMemory(
                self.pe.async_client, self.pe.sync_client, self.pe.engine_config, id
            )
