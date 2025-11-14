import asyncio

from asyncer import asyncify, syncify

from memx.engine.mongodb import MongoDBEngine
from memx.engine.postgres import PostgresEngine
from memx.engine.sqlite import SQLiteEngine


def test_flow_sync(engine):
    m1 = engine.create_session()  # create a new session
    m1.sync.add([{"role": "user", "content": "Hello, how are you?"}])
    m1.sync.add([{"role": "agent", "content": "Fine, thanks for asking"}])

    session_id = m1.get_id()
    print("session_id:", session_id)  # autoassigned session id

    print(m1.sync.get())

    m2 = syncify(engine.get_session, raise_sync_error=False)(id=session_id)  # resume the session
    m2.sync.add([{"role": "user", "content": "What is the capital of France?"}])

    print(syncify(engine.get_session, raise_sync_error=False)(id=session_id).sync.get())


async def test_flow_async(engine):
    m1 = engine.create_session()  # create a new session
    await m1.add([{"role": "user", "content": "Hello, how are you?"}])
    await m1.add([{"role": "agent", "content": "Fine, thanks for asking"}])

    session_id = m1.get_id()
    print("session_id:", session_id)  # autoassigned session id

    print(await m1.get())

    m2 = await engine.get_session(session_id)  # resume the session
    await m2.add([{"role": "user", "content": "What is the capital of France?"}])

    print(await (await engine.get_session(session_id)).get())


async def amain():
    # SQLite backend
    sqlite_uri = "sqlite+aiosqlite:///memx-store.db"
    engine1 = SQLiteEngine(sqlite_uri, "memx-messages", start_up=True)

    await test_flow_async(engine1)

    # PostgreSQL backend
    pg_uri = "postgresql+psycopg://admin:1234@localhost:5433/test-database"
    engine1 = PostgresEngine(pg_uri, "memx-messages", start_up=True)

    await test_flow_async(engine1)

    # MongoDB backend
    mongodb_uri = "mongodb://admin:1234@localhost:27017"
    engine1 = MongoDBEngine(mongodb_uri, "memx-test", "memx-messages")

    await test_flow_async(engine1)


def main():
    # SQLite backend
    sqlite_uri = "sqlite+aiosqlite:///memx-store.db"
    engine1 = SQLiteEngine(sqlite_uri, "memx-messages", start_up=True)

    test_flow_sync(engine1)

    # PostgreSQL backend
    pg_uri = "postgresql+psycopg://admin:1234@localhost:5433/test-database"
    engine1 = PostgresEngine(pg_uri, "memx-messages", start_up=True)

    test_flow_sync(engine1)

    # MongoDB backend
    mongodb_uri = "mongodb://admin:1234@localhost:27017"
    engine1 = MongoDBEngine(mongodb_uri, "memx-test", "memx-messages")

    test_flow_sync(engine1)


if __name__ == "__main__":
    # asyncio.run(amain())
    main()
