import json
from datetime import datetime, timezone
from textwrap import dedent
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.memory import BaseMemory


class PostgresMemory(BaseMemory):
    def __init__(self, uri: str, table: str, schema: str = "public", session_id: str = None):
        self.table_name = f'"{table.strip()}"'
        self.init_queries()

        driver, _ = uri.split(":", 1)
        if driver.strip() != "postgresql+psycopg":
            raise ValueError("For the moment, only 'postgresql+psycopg' driver is supported")

        common_args = {
            "autocommit": False,
            "autoflush": False,
            "expire_on_commit": True,
        }

        self.async_engine = create_async_engine(
            uri,
            connect_args={"options": f"-csearch_path={schema}"},
        )
        self.AsyncSessionCtx = async_sessionmaker(
            **common_args,
            bind=self.async_engine,
            class_=AsyncSession,
        )  # type: ignore

        self.sync_engine = create_engine(
            uri,
            connect_args={"options": f"-csearch_path={schema}"},
        )
        self.SyncSessionCtx = sessionmaker(
            **common_args,
            bind=self.sync_engine,
            class_=Session,
        )  # type: ignore

        with self.SyncSessionCtx() as session:
            session.execute(text(self.table_sql))
            session.commit()

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
            "updated_at": ts_now,
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

        result = result.first()
        result = getattr(result, "message", [])

        return result

    def init_queries(self):
        """."""

        self.table_sql = dedent(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                session_id uuid PRIMARY KEY,
                message JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """)

        self.insert_sql = dedent(f"""
            INSERT INTO {self.table_name} (session_id, message, updated_at) 
            VALUES (:session_id, cast(:message as jsonb), :updated_at)
            ON CONFLICT (session_id) 
            DO UPDATE SET 
                message = COALESCE({self.table_name}.message, '[]'::jsonb) || EXCLUDED.message,
                updated_at = EXCLUDED.updated_at;        
        """)

        self.get_sql = dedent(f"""
            SELECT * FROM {self.table_name}
            WHERE session_id = :session_id;
        """)


class _sync(BaseMemory):
    def __init__(self, parent: "PostgresMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[dict]):
        pass

    def get(self) -> list[dict]:
        pass
