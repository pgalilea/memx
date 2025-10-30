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
    table_sql = """
        CREATE TABLE IF NOT EXISTS '{table_name}' (
            session_id TEXT,
            message JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS session_index ON '{table_name}' (session_id);
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

        with self.sync_engine.begin() as conn:
            conn.connection.executescript(
                self.table_sql.format(table_name=self.table_name)
            )

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

    def add(self, messages: list[dict]):
        insert_sql = f"""
            INSERT INTO '{self.table_name}' (session_id, message, created_at)
            VALUES (:session_id, :message, :created_at);
        """

        ts_now = datetime.now(timezone.utc)
        data = {
            "session_id": self._session_id,
            "message": json.dumps(messages),
            "created_at": ts_now,
        }

        with self.SyncSessionLocal() as session:
            session.execute(text(insert_sql), data)
            session.commit()

    def get(self) -> list[dict]:
        with self.SyncSessionLocal() as session:
            result = session.execute(
                text(
                    dedent(
                        f"""
                        SELECT * FROM '{self.table_name}'
                        WHERE session_id = :session_id 
                        ORDER BY created_at ASC;
                        """
                    )
                ),
                {"session_id": self._session_id},
            )

        result = [dict(row._mapping) for row in result.fetchall()]
        for i in range(len(result)):
            result[i]["message"] = orjson.loads(result[i]["message"])

        return result
