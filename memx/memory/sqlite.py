import json
from datetime import datetime, timezone
from textwrap import dedent
from uuid import uuid4

import orjson
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.memory import BaseMemory


class SQLiteMemory(BaseMemory):
    def __init__(self, uri: str, table: str, session_id: str = None):
        self.table_name = f"'{table.strip()}'"
        self.init_queries()

        self.async_engine = create_async_engine(uri, echo=False, future=True)
        self.AsyncSessionCtx = async_sessionmaker(
            bind=self.async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        drivers, others = uri.split(":", 1)
        self.sync_engine = create_engine(
            f"sqlite:{others}",
            echo=False,
            connect_args={"check_same_thread": True},
        )

        self.SyncSessionCtx = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.sync_engine,
            class_=Session,
        )

        with self.sync_engine.begin() as conn:
            conn.connection.executescript(self.table_sql)

        self.sync = _sync(self)  # to group sync methods

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

    async def add(self, messages: list[dict]):
        ts_now = datetime.now(timezone.utc)
        data = {
            "session_id": self._session_id,
            "message": json.dumps(messages),
            "created_at": ts_now,
        }

        async with self.AsyncSessionCtx() as session:
            await session.execute(text(self.insert_sql), data)
            await session.commit()

    async def get(self) -> list[dict]:
        async with self.AsyncSessionCtx() as session:
            result = await session.execute(
                text(self.get_sql),
                {"session_id": self._session_id},
            )

        result = [dict(row._mapping) for row in result.fetchall()]
        for i in range(len(result)):
            result[i]["message"] = orjson.loads(result[i]["message"])

        return result

    def init_queries(self):
        """."""

        self.table_sql = dedent(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                session_id TEXT,
                message JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS session_index ON {self.table_name} (session_id);
        """)

        self.insert_sql = dedent(f"""
            INSERT INTO {self.table_name} (session_id, message, created_at)
            VALUES (:session_id, :message, :created_at);
        """)

        self.get_sql = dedent(f"""
            SELECT * FROM {self.table_name}
            WHERE session_id = :session_id 
            ORDER BY created_at ASC;
        """)


class _sync(BaseMemory):
    def __init__(self, parent: "SQLiteMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[dict]):
        ts_now = datetime.now(timezone.utc)
        data = {
            "session_id": self.pm._session_id,
            "message": json.dumps(messages),
            "created_at": ts_now,
        }

        with self.pm.SyncSessionCtx() as session:
            session.execute(text(self.pm.insert_sql), data)
            session.commit()

    def get(self) -> list[dict]:
        with self.pm.SyncSessionCtx() as session:
            result = session.execute(
                text(self.pm.get_sql),
                {"session_id": self.pm._session_id},
            )

        result = [dict(row._mapping) for row in result.fetchall()]
        for i in range(len(result)):
            result[i]["message"] = orjson.loads(result[i]["message"])

        return result
