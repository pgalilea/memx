from datetime import UTC, datetime

import redis
from redis.commands.json.path import Path

from memx.memory import BaseMemory
from memx.models import JSON, RedisEngineConfig
from memx.utils.uuid import uuid7


class RedisMemory(BaseMemory):
    def __init__(
        self,
        async_client: redis.asyncio.Redis,  # type: ignore
        sync_client: redis.Redis,
        engine_config: RedisEngineConfig,
        session_id: str = None,
    ):
        self.async_client = async_client
        self.sync_client = sync_client

        self.engine_config = engine_config

        self.sync = _sync(self)  # to group sync methods

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid7())

        # TODO: slice the session_id to avoid long keys (?)
        self.key = f"{self.engine_config.prefix}{self._session_id}"

    async def add(self, messages: list[JSON]):
        ts_now = datetime.now(UTC).isoformat()

        data = {
            "session_id": self._session_id,
            "messages": messages or [],
            "created_at": ts_now,
            "updated_at": ts_now,
        }

        if (await self.async_client.exists(self.key)) == 0:  # does not exist, create it
            await self.async_client.json().set(self.key, Path.root_path(), data)  # type: ignore
            if self.engine_config.ttl is not None:
                await self.async_client.expire(self.key, self.engine_config.ttl)
        else:
            # TODO: merge ops in a transaction
            await self.async_client.json().arrappend(
                self.key, self.engine_config.array_path, *messages
            )  # type: ignore
            await self.async_client.json().set(self.key, Path(".updated_at"), ts_now)  # type: ignore

    async def get(self) -> list[JSON]:
        messages = await self.async_client.json().get(self.key, self.engine_config.array_path)  # type: ignore
        return messages or []

    async def put(self, data: dict):
        await self.add([data])

    async def get_one(self) -> JSON | None:
        messages = await self.get()

        return messages[-1] if messages else None


class _sync(BaseMemory):
    def __init__(self, parent: "RedisMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[JSON]):
        ts_now = datetime.now(UTC).isoformat()

        data = {
            "session_id": self.pm._session_id,
            "messages": messages or [],
            "created_at": ts_now,
            "updated_at": ts_now,
        }

        if (self.pm.sync_client.exists(self.pm.key)) == 0:  # does not exist, create it
            self.pm.sync_client.json().set(self.pm.key, Path.root_path(), data)  # type: ignore
            if self.pm.engine_config.ttl is not None:
                self.pm.sync_client.expire(self.pm.key, self.pm.engine_config.ttl)
        else:
            # TODO: to transaction
            self.pm.sync_client.json().arrappend(
                self.pm.key, self.pm.engine_config.array_path, *messages
            )  # type: ignore
            self.pm.sync_client.json().set(self.pm.key, Path(".updated_at"), ts_now)  # type: ignore

    def get(self) -> list[JSON]:
        messages = self.pm.sync_client.json().get(self.pm.key, self.pm.engine_config.array_path)  # type: ignore
        return messages or []  # type: ignore

    def put(self, data: dict):
        self.pm.sync.add([data])

    def get_one(self) -> JSON | None:
        messages = self.pm.sync.get()

        return messages[-1] if messages else None
