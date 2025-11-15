from unittest.mock import MagicMock, patch

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
