from datetime import datetime, timezone
from uuid import uuid4

from bson.objectid import ObjectId
from pymongo import AsyncMongoClient, MongoClient, ReturnDocument
from pymongo.server_api import ServerApi

from memx.memory import BaseMemory


class MongoDBMemory(BaseMemory):
    # TODO: async client
    def __init__(
        self, uri: str, database: str, collection: str, session_id: str = None
    ):
        self.client = MongoClient(uri)
        self.async_client = AsyncMongoClient(
            uri,
            server_api=ServerApi(version="1", strict=True, deprecation_errors=True),
        )

        self.db = self.client[database]
        self.async_db = self.async_client.get_database(database)

        self.collection = self.db[collection]
        self.async_collection = self.async_db[collection]

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid4())

        # self.sync = self._sync(self)  # to group sync methods

    def add(self, messages: list[dict]):
        _now = datetime.now(timezone.utc)

        self.collection.find_one_and_update(
            {"session_id": self._session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$setOnInsert": {"created_at": _now},
                "$set": {"updated_at": _now},
            },
            upsert=True,
        )

    def get(self) -> list[dict]:
        doc = self.collection.find_one({"session_id": self._session_id})

        return (doc or {}).get("messages", [])
