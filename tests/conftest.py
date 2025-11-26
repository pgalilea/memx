from collections.abc import Generator
from dataclasses import dataclass

import pytest
from testcontainers.mongodb import MongoDbContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@dataclass(frozen=True)
class MongoDBConnection:
    url: str
    db: str
    collection: str


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    container = PostgresContainer("postgres:16-alpine", driver="psycopg")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def postgres_uri(postgres_container: PostgresContainer) -> str:
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    container = RedisContainer("redis:8-alpine")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def redis_uri(redis_container: RedisContainer) -> str:
    _redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    return _redis_url


@pytest.fixture(scope="session")
def mongodb_container() -> Generator[MongoDbContainer, None, None]:
    container = MongoDbContainer("mongo:latest")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def mongodb_cnx(mongodb_container: MongoDbContainer) -> MongoDBConnection:
    return MongoDBConnection(
        url=mongodb_container.get_connection_url(), db="memx-test", collection="memx-messages"
    )
