import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def postgres_container():
    container = PostgresContainer("postgres:16-alpine", driver="psycopg")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def postgres_uri(postgres_container):
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def redis_container():
    container = RedisContainer("redis:8-alpine")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def redis_uri(redis_container):
    _redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    return _redis_url
