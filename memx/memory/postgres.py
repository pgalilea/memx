from datetime import UTC, datetime
from uuid import uuid4

import orjson
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from memx.memory import BaseMemory
from memx.models.sql import SQLEngineConfig


class PostgresMemory(BaseMemory):
    def __init__(
        self,
        async_session_maker: async_sessionmaker[AsyncSession],  # type: ignore
        sync_session_maker: sessionmaker[Session],
        engine_config: SQLEngineConfig,
        session_id: str = None,
    ):
        self.AsyncSession = async_session_maker
        self.SyncSession = sync_session_maker

        self.engine_config = engine_config

        self.sync = _sync(self)  # to group sync methods

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

    async def add(self, messages: list[dict]):
        # TODO: refactor this with sqlite
        await self._pre_add()

        ts_now = datetime.now(UTC)
        data = {
            "session_id": self._session_id,
            "message": orjson.dumps(messages).decode("utf-8"),
            "updated_at": ts_now,
        }

        async with self.AsyncSession() as session:
            await session.execute(text(self.engine_config.add_query), data)
            await session.commit()

    async def get(self) -> list[dict]:
        async with self.AsyncSession() as session:
            result = await session.execute(
                text(self.engine_config.get_query),
                {"session_id": self._session_id},
            )

        result = result.first()
        result = getattr(result, "message", [])

        return result

    async def _pre_add(self):
        pass


class _sync(BaseMemory):
    def __init__(self, parent: "PostgresMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[dict]):
        # TODO: refactor this with sqlite

        self._pre_add()

        ts_now = datetime.now(UTC)
        data = {
            "session_id": self.pm._session_id,
            "message": orjson.dumps(messages).decode("utf-8"),
            "updated_at": ts_now,
        }

        with self.pm.SyncSession() as session:
            session.execute(text(self.pm.engine_config.add_query), data)
            session.commit()

    def get(self) -> list[dict]:
        with self.pm.SyncSession() as session:
            result = session.execute(
                text(self.pm.engine_config.get_query),
                {"session_id": self.pm._session_id},
            )

        result = result.first()
        result = getattr(result, "message", [])

        return result

    def _pre_add(self):
        pass
