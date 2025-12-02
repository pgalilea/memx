from textwrap import dedent

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.engine import BaseEngine
from memx.memory.sqlite import SQLiteMemory
from memx.models.sql import SQLEngineConfig
from memx.services import sql_service


class SQLiteEngine(BaseEngine):
    def __init__(self, uri: str, table: str, start_up: bool = False):
        """Initialize SQLite engine for memory storage.

        Args:
            uri: Database connection URI for SQLite.
            table: Name of the table to use for storing memories.
            start_up: If True, create the table if it doesn't exist (blocking operation).
        """

        self.table_name = f"'{table.strip()}'"
        self._init_queries()

        self.async_engine = create_async_engine(uri, echo=False, future=True)
        self.AsyncSession = async_sessionmaker(
            bind=self.async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        drivers, others = uri.split(":", 1)  # type: ignore[reportUnusedVariable]
        self.sync_engine = create_engine(
            f"sqlite:{others}",
            echo=False,
            connect_args={"check_same_thread": True},
        )

        self.SyncSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.sync_engine,
            class_=Session,
        )

        self.sync = _sync(self)

        if start_up:
            self.start_up()  # blocking operation

    def create_session(self) -> SQLiteMemory:
        """Create a local memory session."""

        engine_config = SQLEngineConfig(
            table=self.table_name,
            add_query=self.add_sql,
            get_query=self.get_sql,
        )
        return SQLiteMemory(self.AsyncSession, self.SyncSession, engine_config)

    async def get_session(self, id: str) -> SQLiteMemory | None:
        """Get a memory session."""

        if engine_config := await sql_service.get_session(self, id):
            return SQLiteMemory(self.AsyncSession, self.SyncSession, engine_config, id)

        return None  # explicit is better than implicit

    def _init_queries(self):
        """Initialize the queries for the engine."""

        self.table_sql = dedent(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                session_id TEXT,
                message JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS session_index ON {self.table_name} (session_id);
        """)

        self.add_sql = dedent(f"""
            INSERT INTO {self.table_name} (session_id, message, created_at)
            VALUES (:session_id, :message, :created_at);
        """)

        self.get_sql = dedent(f"""
            SELECT message FROM {self.table_name}
            WHERE session_id = :session_id
            ORDER BY created_at ASC;
        """)

        self.get_session_sql = dedent(f"""
            SELECT EXISTS(
                SELECT 1 FROM {self.table_name}
                WHERE session_id=:session_id
            ) as r;
        """)

    def start_up(self):
        """Create the table if it doesn't exist."""

        with self.sync_engine.begin() as conn:
            conn.connection.executescript(self.table_sql)


class _sync:
    def __init__(self, parent: "SQLiteEngine"):
        self.pe = parent

    def get_session(self, id: str) -> SQLiteMemory | None:
        """Get a memory session."""

        if engine_config := sql_service.get_session_sync(self.pe, id):
            return SQLiteMemory(self.pe.AsyncSession, self.pe.SyncSession, engine_config, id)

        return None  # explicit is better than implicit
