import pytest

from memx.memory.simple import DiskMemory, InMemory


pytestmark = pytest.mark.filterwarnings("ignore:.*:DeprecationWarning")


def test_put_and_get_one_sync(tmp_path):
    m1 = DiskMemory(dir=tmp_path)

    assert m1.sync.get_one() is None

    data = {"user": "alice", "preferences": {"language": "en"}}
    m1.sync.put(data)

    assert m1.sync.get() == [data]
    assert m1.sync.get_one() == data


async def test_put_and_get_one_async(tmp_path):
    m1 = DiskMemory(dir=tmp_path)

    assert await m1.get_one() is None

    data = {"user": "bob", "preferences": {"language": "es"}}
    await m1.put(data)

    assert await m1.get() == [data]
    assert await m1.get_one() == data


def test_put_and_get_one_in_memory():
    m1 = InMemory()

    assert m1.get_one() is None

    data = {"user": "alice", "preferences": {"language": "en"}}
    m1.put(data)

    assert m1.get() == [data]
    assert m1.get_one() == data
