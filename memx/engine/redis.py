import redis
from redis.commands.json.path import Path

from memx.engine import BaseEngine
from memx.memory.redis import RedisMemory


class RedisEngine(BaseEngine):
    def __init__(self, uri: str, start_up: bool = False, **kwargs):
        # TODO: handle kwargs
        self.sync_client = redis.Redis.from_url(uri, decode_responses=True)
        self.async_client = redis.asyncio.Redis.from_url(uri, decode_responses=True)  # type: ignore

        self.sync = _sync(self)

        if start_up:
            self.start_up()  # blocking operation

    def create_session(self) -> RedisMemory:
        return RedisMemory(self.async_client, self.sync_client)

    async def get_session(self, session_id: str) -> RedisMemory | None:
        if (await self.async_client.exists(session_id)) > 0:
            return RedisMemory(self.async_client, self.sync_client, session_id)

    def start_up(self):
        """Create the Redis key if it doesn't exist."""

        # self.sync_client.ping()
        # self.sync_client.info()
        try:
            # NOTE: Starting with Redis 8, the JSON data structure is integral to Redis.
            # https://github.com/RedisJSON/RedisJSON
            self.sync_client.json().get("memx", Path.root_path())
        except Exception as e:
            raise RuntimeError("RedisJSON not found") from e


class _sync:
    """Sync methods for RedisEngine."""

    def __init__(self, parent: "RedisEngine"):
        self.pe = parent

    def get_session(self, session_id: str) -> RedisMemory | None:
        if self.pe.sync_client.exists(session_id) > 0:  # type: ignore
            return RedisMemory(self.pe.async_client, self.pe.sync_client, session_id)
