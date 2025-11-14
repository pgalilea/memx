from datetime import UTC, datetime
from uuid import uuid4

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.collection import Collection

from memx.memory import BaseMemory


class MongoDBMemory(BaseMemory):
    def __init__(
        self,
        async_collection: AsyncCollection,
        sync_collection: Collection,
        session_id: str = None,
    ):
        self.async_collection = async_collection
        self.sync_collection = sync_collection

        self.sync = _sync(self)  # to group sync methods

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

    async def add(self, messages: list[dict]):
        ts_now = datetime.now(UTC)

        await self.async_collection.find_one_and_update(
            {"session_id": self._session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$setOnInsert": {"created_at": ts_now},
                "$set": {"updated_at": ts_now},
            },
            upsert=True,
        )

    async def get(self) -> list[dict]:
        doc = await self.async_collection.find_one({"session_id": self._session_id})

        return (doc or {}).get("messages", [])


class _sync(BaseMemory):
    def __init__(self, parent: "MongoDBMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[dict]):
        ts_now = datetime.now(UTC)

        self.pm.sync_collection.find_one_and_update(
            {"session_id": self.pm._session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$setOnInsert": {"created_at": ts_now},
                "$set": {"updated_at": ts_now},
            },
            upsert=True,
        )

    def get(self) -> list[dict]:
        doc = self.pm.sync_collection.find_one({"session_id": self.pm._session_id})

        return (doc or {}).get("messages", [])
