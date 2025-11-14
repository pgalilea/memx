from datetime import UTC, datetime
from uuid import uuid4

from pymongo import AsyncMongoClient, MongoClient
from pymongo.server_api import ServerApi

from memx.engine import BaseEngine
from memx.memory.mongodb import MongoDBMemory


class MongoDBEngine(BaseEngine):
    def __init__(self, uri: str, database: str, collection: str):
        """MongoDB memory engine."""

        self.client = MongoClient(uri)
        self.async_client = AsyncMongoClient(
            uri,
            server_api=ServerApi(version="1", strict=True, deprecation_errors=True),
        )

        self.db = self.client[database]
        self.async_db = self.async_client.get_database(database)

        self.sync_collection = self.db[collection]
        self.async_collection = self.async_db[collection]

    def get_session(self, session_id: str = None) -> MongoDBMemory:
        """Get or create a memory session."""

        return MongoDBMemory(self.async_collection, self.sync_collection, session_id)
