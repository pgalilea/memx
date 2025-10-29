import asyncio

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from memx.memory import BaseMemory


class PostgresMemory(BaseMemory):
    def __init__(self, uri: str, database: str, collection: str):
        pass

    def add(self, messages: list[dict]):
        self.collection.insert_one(messages)

    def get(self) -> list[dict]:
        return self.collection.find_one()
