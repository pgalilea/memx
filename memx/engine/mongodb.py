from pymongo import AsyncMongoClient, MongoClient
from pymongo.server_api import ServerApi

from memx.engine import BaseEngine
from memx.memory.mongodb import MongoDBMemory


class MongoDBEngine(BaseEngine):
    def __init__(self, uri: str, database: str, collection: str):
        """MongoDB memory engine."""

        self.sync_client = MongoClient(uri)
        self.async_client = AsyncMongoClient(
            uri,
            server_api=ServerApi(version="1", strict=True, deprecation_errors=True),
        )

        self.sync_db = self.sync_client[database]
        self.async_db = self.async_client.get_database(database)

        self.sync_collection = self.sync_db[collection]
        self.async_collection = self.async_db[collection]

        self.sync = _sync(self)

    def create_session(self) -> MongoDBMemory:
        return MongoDBMemory(self.async_collection, self.sync_collection)

    async def get_session(self, id: str) -> MongoDBMemory | None:
        result = await self.async_collection.find_one({"session_id": id})

        if result:
            return MongoDBMemory(self.async_collection, self.sync_collection, id)


class _sync:
    """Sync methods for MongoDBEngine."""

    def __init__(self, parent: "MongoDBEngine"):
        self.pe = parent

    def get_session(self, id: str) -> MongoDBMemory | None:
        """Get a memory session."""

        if self.pe.sync_collection.find_one({"session_id": id}, {"_id": 1}) is not None:
            return MongoDBMemory(self.pe.async_collection, self.pe.sync_collection, id)
