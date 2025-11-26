from inspect import iscoroutinefunction
from uuid import uuid4

from memx.engine.postgres import PostgresEngine


def test_engine_init(postgres_uri: str):
    engine = PostgresEngine(postgres_uri, "memx-messages", start_up=True)
    assert engine.table_name == '"memx-messages"'
    assert engine.async_engine is not None
    assert engine.sync_engine is not None
    assert engine.AsyncSession is not None
    assert engine.SyncSession is not None
    assert callable(engine.sync.get_session)
    assert iscoroutinefunction(engine.get_session)
    assert isinstance(engine.table_sql, str) and len(engine.table_sql) > 0
    assert isinstance(engine.add_sql, str) and len(engine.add_sql) > 0
    assert isinstance(engine.get_sql, str) and len(engine.get_sql) > 0
    assert isinstance(engine.get_session_sql, str) and len(engine.get_session_sql) > 0


async def test_simple_add_async(postgres_uri: str):
    engine = PostgresEngine(postgres_uri, f"memx-messages-{uuid4()}"[:-28], start_up=True)
    m1 = engine.create_session()
    messages = [{"role": "user", "content": "Hello, how are you?"}]

    await m1.add(messages)

    assert await m1.get() == messages

    new_message = [{"role": "agent", "content": "Fine, thanks for asking"}]
    messages.extend(new_message)

    await m1.add(new_message)

    result = await m1.get()
    assert result == messages


def test_resume_session_sync(postgres_uri: str):
    engine = PostgresEngine(postgres_uri, f"memx-messages-{uuid4()}"[:-28], start_up=True)
    m1 = engine.create_session()
    messages = [
        {"role": "system", "content": "You are a poetry expert"},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "Cherry blossoms bloom..."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "Paris"},
    ]
    m1.sync.add(messages)
    assert m1.sync.get() == messages

    m2 = engine.sync.get_session(m1.get_id())
    new_messages = [
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    m2.sync.add(new_messages)  # type: ignore
    messages.extend(new_messages)

    assert m2.sync.get() == messages  # type: ignore
    assert m1.sync.get() == m2.sync.get()  # type: ignore
    assert engine.sync.get_session(uuid4()) is None
    assert m1.get_id() == m2.get_id()  # type: ignore


async def test_resume_session_async(postgres_uri: str):
    engine = PostgresEngine(postgres_uri, f"memx-messages-{uuid4()}"[:-28], start_up=True)
    m1 = engine.create_session()
    messages = [
        {"role": "system", "content": "You are a poetry expert"},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "Cherry blossoms bloom..."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "Paris"},
    ]
    await m1.add(messages)
    assert await m1.get() == messages

    m2 = await engine.get_session(m1.get_id())
    new_messages = [
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    await m2.add(new_messages)  # type: ignore
    messages.extend(new_messages)

    assert await m2.get() == messages  # type: ignore
    assert await m1.get() == m2.sync.get()  # type: ignore
    assert await engine.get_session(uuid4()) is None
    assert m1.get_id() == m2.get_id()  # type: ignore
