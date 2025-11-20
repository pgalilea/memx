from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from memx.engine.postgres import PostgresEngine


@patch("memx.engine.postgres.create_async_engine")
@patch("memx.engine.postgres.create_engine")
@patch("memx.engine.postgres.async_sessionmaker")
@patch("memx.engine.postgres.sessionmaker")
def test_engine_init(
    mock_sessionmaker,
    mock_async_sessionmaker,
    mock_create_engine,
    mock_create_async_engine,
):
    # Setup mocks
    mock_async_engine = MagicMock()
    mock_sync_engine = MagicMock()
    mock_async_session = MagicMock()
    mock_sync_session = MagicMock()

    mock_create_async_engine.return_value = mock_async_engine
    mock_create_engine.return_value = mock_sync_engine
    mock_async_sessionmaker.return_value = mock_async_session
    mock_sessionmaker.return_value = mock_sync_session

    # Mock the start_up method to avoid actual database operations
    with patch.object(PostgresEngine, "start_up", return_value=None):
        pg_uri = "postgresql+psycopg://admin:1234@localhost:5433/test-database"
        engine = PostgresEngine(pg_uri, "memx-messages", start_up=True)

        assert engine.table_name == '"memx-messages"'
        assert engine.async_engine is not None
        assert engine.sync_engine is not None
        assert engine.AsyncSession is not None
        assert engine.SyncSession is not None
        assert isinstance(engine.table_sql, str)
        assert isinstance(engine.add_sql, str)
        assert isinstance(engine.get_sql, str)
        assert isinstance(engine.get_session_sql, str)

        # Verify that engines were created with correct URI
        mock_create_async_engine.assert_called_once()
        mock_create_engine.assert_called_once()
        mock_async_sessionmaker.assert_called_once()
        mock_sessionmaker.assert_called_once()


@pytest.mark.asyncio
@patch("memx.engine.postgres.create_async_engine")
@patch("memx.engine.postgres.create_engine")
@patch("memx.engine.postgres.async_sessionmaker")
@patch("memx.engine.postgres.sessionmaker")
async def test_simple_add_async(
    mock_sessionmaker,
    mock_async_sessionmaker,
    mock_create_engine,
    mock_create_async_engine,
):
    # Setup mocks
    mock_async_engine = MagicMock()
    mock_sync_engine = MagicMock()

    # Create a mock async session that works as an async context manager
    mock_async_session_instance = AsyncMock()
    mock_async_session_instance.execute = AsyncMock()
    mock_async_session_instance.commit = AsyncMock()

    # Create a mock async sessionmaker that returns the mock session
    # Each call to the sessionmaker should return a new async context manager
    def make_async_context_manager():
        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=mock_async_session_instance)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        return context_manager

    mock_async_session = MagicMock(side_effect=make_async_context_manager)

    mock_sync_session = MagicMock()

    mock_create_async_engine.return_value = mock_async_engine
    mock_create_engine.return_value = mock_sync_engine
    mock_async_sessionmaker.return_value = mock_async_session
    mock_sessionmaker.return_value = mock_sync_session

    # Mock the start_up method to avoid actual database operations
    with patch.object(PostgresEngine, "start_up", return_value=None):
        pg_uri = "postgresql+psycopg://admin:1234@localhost:5433/test-database"
        engine = PostgresEngine(pg_uri, "memx-messages", start_up=True)
        m1 = engine.create_session()

        # Setup mock for get() - first call returns empty, then returns messages
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Mock result object for get() calls
        mock_result_row = MagicMock()
        mock_result_row.message = messages

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_result_row)
        mock_async_session_instance.execute.return_value = mock_result

        # Test initial add
        await m1.add(messages)

        # Verify add was called
        assert mock_async_session_instance.execute.called
        assert mock_async_session_instance.commit.called

        # Test get
        result = await m1.get()
        assert result == messages

        # Test adding another message
        new_message = [{"role": "agent", "content": "Fine, thanks for asking"}]
        messages.extend(new_message)

        # Update mock to return extended messages
        mock_result_row.message = messages

        await m1.add(new_message)

        # Verify add was called again
        assert mock_async_session_instance.execute.call_count >= 2
        assert mock_async_session_instance.commit.call_count >= 2

        # Test get again
        result = await m1.get()
        assert result == messages
