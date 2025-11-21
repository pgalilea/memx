from uuid import uuid4

import orjson
from sqlalchemy import Result, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from memx.memory import BaseMemory
from memx.models import JSON
from memx.models.sql import SQLEngineConfig
from memx.services import sql_service


class SQLiteMemory(BaseMemory):
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

    async def add(self, messages: list[JSON]):
        await self._pre_add()

        data = sql_service.format_messages(self._session_id, messages)

        async with self.AsyncSession() as session:
            await session.execute(text(self.engine_config.add_query), data)
            await session.commit()

    async def get(self) -> list[JSON]:
        async with self.AsyncSession() as session:
            result = await session.execute(
                text(self.engine_config.get_query),
                {"session_id": self._session_id},
            )

        messages = _merge_messages(result)

        return messages

    async def _pre_add(self):
        pass


class _sync(BaseMemory):
    def __init__(self, parent: "SQLiteMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[JSON]):
        self._pre_add()

        data = sql_service.format_messages(self.pm._session_id, messages)

        with self.pm.SyncSession() as session:
            session.execute(text(self.pm.engine_config.add_query), data)
            session.commit()

    def get(self) -> list[JSON]:
        with self.pm.SyncSession() as session:
            result = session.execute(
                text(self.pm.engine_config.get_query),
                {"session_id": self.pm._session_id},
            )

        messages = _merge_messages(result)

        return messages  # type: ignore

    def _pre_add(self):
        pass


def _merge_messages(msg_result: Result) -> list[JSON]:
    """Merge messages from the result of the query."""

    # list.extend is the fastest approach
    result = [dict(row._mapping) for row in msg_result.fetchall()]
    messages = []

    for r in result:
        messages.extend(orjson.loads(r["message"]))

    return messages
