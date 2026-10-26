from unittest.mock import AsyncMock

from memx.engine.mongodb import MongoDBEngine
from memx.engine.postgres import PostgresEngine
from memx.engine.redis import RedisEngine
from memx.engine.sqlite import SQLiteEngine


async def test_postgres_close(mocker):
    """close() disposes the async engine; sync.close() disposes the sync engine."""

    engine = PostgresEngine("postgresql+psycopg://u:p@localhost:5432/memx", "memx")
    dispose = mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncEngine.dispose", new_callable=AsyncMock
    )
    sync_dispose = mocker.patch.object(engine.sync_engine, "dispose")

    await engine.close()
    dispose.assert_awaited_once()

    engine.sync.close()
    sync_dispose.assert_called_once()


async def test_sqlite_close(mocker):
    """close() disposes the async engine; sync.close() disposes the sync engine."""

    engine = SQLiteEngine("sqlite+aiosqlite:///:memory:", "memx")
    dispose = mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncEngine.dispose", new_callable=AsyncMock
    )
    sync_dispose = mocker.patch.object(engine.sync_engine, "dispose")

    await engine.close()
    dispose.assert_awaited_once()

    engine.sync.close()
    sync_dispose.assert_called_once()


async def test_redis_close(mocker):
    """close() closes the async client; sync.close() closes the sync client."""

    engine = RedisEngine("redis://localhost:6379")
    aclose = mocker.patch.object(engine.async_client, "aclose", new_callable=AsyncMock)
    close = mocker.patch.object(engine.sync_client, "close")

    await engine.close()
    aclose.assert_awaited_once()

    engine.sync.close()
    close.assert_called_once()


async def test_mongodb_close(mocker):
    """close() closes the async client; sync.close() closes the sync client."""

    engine = MongoDBEngine("mongodb://localhost:27017", "memx-test", "memx-messages")
    aclose = mocker.patch.object(engine.async_client, "close", new_callable=AsyncMock)
    close = mocker.patch.object(engine.sync_client, "close")

    await engine.close()
    aclose.assert_awaited_once()

    engine.sync.close()
    close.assert_called_once()
