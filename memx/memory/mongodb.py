from datetime import UTC, datetime
from uuid import uuid4

from pymongo import AsyncMongoClient, MongoClient
from pymongo.server_api import ServerApi

from memx.memory import BaseMemory


class MongoDBMemory(BaseMemory):
    def __init__(self, uri: str, database: str, collection: str, session_id: str = None):
        self.client = MongoClient(uri)
        self.async_client = AsyncMongoClient(
            uri,
            server_api=ServerApi(version="1", strict=True, deprecation_errors=True),
        )

        self.db = self.client[database]
        self.async_db = self.async_client.get_database(database)

        self.collection = self.db[collection]
        self.async_collection = self.async_db[collection]

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

        self.pm.collection.find_one_and_update(
            {"session_id": self.pm._session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$setOnInsert": {"created_at": ts_now},
                "$set": {"updated_at": ts_now},
            },
            upsert=True,
        )

    def get(self) -> list[dict]:
        doc = self.pm.collection.find_one({"session_id": self.pm._session_id})

        return (doc or {}).get("messages", [])
