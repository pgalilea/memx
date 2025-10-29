import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.memory import BaseMemory


class SQLiteMemory(BaseMemory):
    table_sql = """
        CREATE TABLE IF NOT EXISTS '{table_name}' (
            id TEXT PRIMARY KEY, -- session_id
            messages JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    def __init__(self, uri: str, table: str, session_id: str = None):
        self.table_name = table.strip()

        self.async_engine = create_async_engine(uri, echo=False, future=True)
        self.AsyncSessionLocal = async_sessionmaker(
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

        self.SyncSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.sync_engine,
            class_=Session,
        )

        with self.SyncSessionLocal() as session:
            session.execute(text(self.table_sql.format(table_name=self.table_name)))
            session.commit()

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

    def add(self, messages: list[dict]):
        # TODO: append messages to existing messages
        upsert_sql = f"""
            INSERT INTO '{self.table_name}' (id, messages, created_at, updated_at)
            VALUES (:id, :messages, :created_at, :updated_at)
            ON CONFLICT (id) DO UPDATE SET
            messages = :messages,
            updated_at = :updated_at
        """

        ts_now = datetime.now(timezone.utc)
        data = {
            "id": self._session_id,
            "messages": json.dumps(messages),
            "created_at": ts_now,
            "updated_at": ts_now,
        }

        with self.SyncSessionLocal() as session:
            session.execute(text(upsert_sql), data)
            session.commit()

    def get(self) -> list[dict]:
        # TODO: implement
        pass
