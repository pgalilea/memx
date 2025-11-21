import redis

from memx.engine import BaseEngine
from memx.memory.redis import RedisMemory


class RedisEngine(BaseEngine):
    def __init__(self, uri: str, **kwargs):
        raise NotImplementedError("RedisEngine is not implemented yet")
        # TODO: handle kwargs
        self.sync_client = redis.Redis.from_url(uri, decode_responses=True)
        self.async_client = redis.asyncio.Redis.from_url(uri, decode_responses=True)  # type: ignore

        # print(self.sync_client.ping())
        self.sync = _sync(self)

    def create_session(self) -> RedisMemory:
        return RedisMemory(self.async_client, self.sync_client)

    async def get_session(self, session_id: str) -> RedisMemory | None:
        if (await self.async_client.exists(session_id)) > 0:
            return RedisMemory(self.async_client, self.sync_client, session_id)


class _sync:
    """Sync methods for RedisEngine."""

    def __init__(self, parent: "RedisEngine"):
        self.pe = parent

    def get_session(self, session_id: str) -> RedisMemory | None:
        if self.pe.sync_client.exists(session_id) > 0:  # type: ignore
            return RedisMemory(self.pe.async_client, self.pe.sync_client, session_id)
