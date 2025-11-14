from datetime import UTC, datetime
from textwrap import dedent
from uuid import uuid4

import orjson
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.engine import BaseEngine
from memx.engine.config import SQLEngineConfig
from memx.memory.postgres import PostgresMemory


class PostgresEngine(BaseEngine):
    def __init__(self, uri: str, table: str, schema: str = "public", start_up: bool = None):
        """."""

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
        self.AsyncSession = async_sessionmaker(
            **common_args,
            bind=self.async_engine,
            class_=AsyncSession,
        )  # type: ignore

        self.sync_engine = create_engine(
            uri,
            connect_args={"options": f"-csearch_path={schema}"},
        )
        self.SyncSession = sessionmaker(
            **common_args,
            bind=self.sync_engine,
            class_=Session,
        )  # type: ignore

        if start_up:
            self.start_up()  # blocking operation

    def create_session(self) -> PostgresMemory:
        """Get or create a memory session."""

        engine_config = SQLEngineConfig(
            table=self.table_name,
            add_query=self.add_sql,
            get_query=self.get_sql,
        )
        return PostgresMemory(self.AsyncSession, self.SyncSession, engine_config)

    async def get_session(self, id: str) -> PostgresMemory | None:
        """Get a memory session."""

        async with self.AsyncSession() as session:
            result = (
                await session.execute(
                    text(self.get_session_sql),
                    {"session_id": id},
                )
            ).first()

        if result[0] == 1:  # type: ignore
            engine_config = SQLEngineConfig(
                table=self.table_name,
                add_query=self.add_sql,
                get_query=self.get_sql,
            )
            return PostgresMemory(self.AsyncSession, self.SyncSession, engine_config, id)

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

        self.add_sql = dedent(f"""
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

        self.get_session_sql = dedent(f"""
            SELECT EXISTS(
                SELECT 1 FROM {self.table_name}
                WHERE session_id=:session_id
            ) as r;
        """)

    def start_up(self):
        """Create the table if it doesn't exist."""

        with self.SyncSession() as session:
            session.execute(text(self.table_sql))
            session.commit()
