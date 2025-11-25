import tempfile
from inspect import iscoroutinefunction
from pathlib import Path

from memx.engine.sqlite import SQLiteEngine


def test_engine_init():
    sqlite_uri = "sqlite+aiosqlite:///:memory:"
    engine = SQLiteEngine(sqlite_uri, "test-messages", start_up=True)
    assert engine.table_name == "'test-messages'"
    assert engine.async_engine is not None
    assert engine.sync_engine is not None
    assert engine.AsyncSession is not None
    assert engine.SyncSession is not None
    assert callable(engine.sync.get_session)
    assert iscoroutinefunction(engine.get_session)
    assert isinstance(engine.add_sql, str)
    assert isinstance(engine.get_sql, str)
    assert isinstance(engine.get_session_sql, str)


def test_same_session_attributes():
    sqlite_uri = "sqlite+aiosqlite:///:memory:"
    engine1 = SQLiteEngine(sqlite_uri, "test-messages", start_up=True)
    m1 = engine1.create_session()
    m2 = engine1.create_session()

    assert m1.SyncSession == m2.SyncSession
    assert m1.AsyncSession == m2.AsyncSession
    assert m1.engine_config == m2.engine_config


def test_simple_add():
    sqlite_uri = "sqlite+aiosqlite:///:memory:"
    engine = SQLiteEngine(sqlite_uri, "test-messages", start_up=True)
    m1 = engine.create_session()

    messages = [{"role": "user", "content": "Hello, how are you?"}]
    m1.sync.add(messages)

    assert m1.sync.get() == messages

    new_message = [{"role": "agent", "content": "Fine, thanks for asking"}]
    m1.sync.add(new_message)
    messages.extend(new_message)

    assert m1.sync.get() == messages


def test_resume_session():
    sqlite_uri = "sqlite+aiosqlite:///:memory:"
    engine = SQLiteEngine(sqlite_uri, "test-messages", start_up=True)
    m1 = engine.create_session()
    session_id = m1.get_id()

    messages = [{"role": "user", "content": "Hello, how are you?"}]
    m1.sync.add(messages)

    assert m1.sync.get() == messages

    m2 = engine.sync.get_session(m1.get_id())

    assert m2.sync.get() == messages  # type: ignore
    assert m1.sync.get() == m2.sync.get()  # type: ignore
    assert engine.sync.get_session("asdf") is None
    assert m1.get_id() == session_id == m2.get_id()  # type: ignore


async def test_simple_add_async():
    fp = tempfile.gettempdir() + "/memx-test.db"
    sqlite_uri = f"sqlite+aiosqlite:///{fp}"
    engine = SQLiteEngine(sqlite_uri, "test-messages", start_up=True)
    m1 = engine.create_session()

    messages = [{"role": "user", "content": "Hello, how are you?"}]
    await m1.add(messages)

    assert await m1.get() == messages

    new_message = [{"role": "agent", "content": "Fine, thanks for asking"}]
    await m1.add(new_message)
    messages.extend(new_message)

    assert await m1.get() == messages

    Path(fp).unlink()


async def test_resume_session_async():
    fp = tempfile.gettempdir() + "/memx-test.db"
    sqlite_uri = f"sqlite+aiosqlite:///{fp}"
    engine = SQLiteEngine(sqlite_uri, "test-messages", start_up=True)
    m1 = engine.create_session()

    messages = [{"role": "user", "content": "Hello, how are you?"}]
    await m1.add(messages)

    assert await m1.get() == messages

    m2 = await engine.get_session(m1.get_id())

    assert await m2.get() == messages  # type: ignore
    assert await m1.get() == await m2.get()  # type: ignore
    assert await engine.get_session("asdf-11!!") is None

    Path(fp).unlink()
