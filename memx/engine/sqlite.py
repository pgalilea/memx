from textwrap import dedent

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.engine import BaseEngine
from memx.engine.config import SQLEngineConfig
from memx.memory.sqlite import SQLiteMemory


class SQLiteEngine(BaseEngine):
    def __init__(self, uri: str, table: str, start_up: bool = False):
        """SQLite memory engine."""

        self.table_name = f"'{table.strip()}'"
        self.init_queries()

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
            return SQLiteMemory(self.AsyncSession, self.SyncSession, engine_config, id)

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
