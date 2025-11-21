from uuid import uuid4

import redis

from memx.memory import BaseMemory
from memx.models import JSON


class RedisMemory(BaseMemory):
    def __init__(
        self, async_client: redis.asyncio.Redis, sync_client: redis.Redis, session_id: str = None
    ):
        self.async_client = async_client
        self.sync_client = sync_client

        self.sync = _sync(self)  # to group sync methods

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

    def add(self, messages: list[JSON]):
        pass

    def get(self) -> list[JSON]:
        pass


class _sync(BaseMemory):
    def __init__(self, parent: "RedisMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[JSON]):
        pass

    def get(self) -> list[JSON]:
        pass
