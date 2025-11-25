from inspect import iscoroutinefunction
from uuid import uuid4

import pytest

from memx.engine.mongodb import MongoDBEngine
from tests.conftest import MongoDBConnection

# Ignore deprecation warning from testcontainers
pytestmark = pytest.mark.filterwarnings("ignore:The wait_for_logs function.*:DeprecationWarning")


def test_engine_init(mongodb_cnx: MongoDBConnection):
    engine = MongoDBEngine(mongodb_cnx.url, mongodb_cnx.db, mongodb_cnx.collection)
    assert engine.sync_collection is not None
    assert engine.async_collection is not None
    assert engine.sync is not None
    assert callable(engine.sync.get_session) is True
    assert iscoroutinefunction(engine.get_session)


async def test_simple_add_async(mongodb_cnx: MongoDBConnection):
    engine = MongoDBEngine(mongodb_cnx.url, mongodb_cnx.db, mongodb_cnx.collection)
    m1 = engine.create_session()
    messages = [{"role": "user", "content": "Hello, how are you?"}]

    await m1.add(messages)

    assert await m1.get() == messages

    new_message = [{"role": "agent", "content": "Fine, thanks for asking"}]
    messages.extend(new_message)

    await m1.add(new_message)

    result = await m1.get()
    assert result == messages

    await engine.async_client.aclose()


def test_resume_session_sync(mongodb_cnx: MongoDBConnection):
    engine = MongoDBEngine(mongodb_cnx.url, mongodb_cnx.db, mongodb_cnx.collection)
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
    assert engine.sync.get_session(str(uuid4())) is None
    assert m1.get_id() == m2.get_id()  # type: ignore
