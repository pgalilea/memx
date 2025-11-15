from typing import TYPE_CHECKING, Union

from sqlalchemy import text

from memx.models.sql import SQLEngineConfig

if TYPE_CHECKING:
    from memx.engine.postgres import PostgresEngine
    from memx.engine.sqlite import SQLiteEngine


async def get_session(
    sql_engine: Union["PostgresEngine", "SQLiteEngine"], id: str
) -> SQLEngineConfig | None:
    """."""

    async with sql_engine.AsyncSession() as session:
        result = (
            await session.execute(
                text(sql_engine.get_session_sql),
                {"session_id": id},
            )
        ).first()

    if result[0] == 1:  # type: ignore
        engine_config = SQLEngineConfig(
            table=sql_engine.table_name,
            add_query=sql_engine.add_sql,
            get_query=sql_engine.get_sql,
        )
        return engine_config


def get_session_sync(
    sql_engine: Union["PostgresEngine", "SQLiteEngine"], id: str
) -> SQLEngineConfig | None:
    """."""

    with sql_engine.SyncSession() as session:
        result = session.execute(text(sql_engine.get_session_sql), {"session_id": id}).first()

    if result[0] == 1:  # type: ignore
        engine_config = SQLEngineConfig(
            table=sql_engine.table_name,
            add_query=sql_engine.add_sql,
            get_query=sql_engine.get_sql,
        )
        return engine_config
