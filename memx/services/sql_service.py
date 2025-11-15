from typing import TYPE_CHECKING, Union

from sqlalchemy import text

from memx.models.sql import SQLEngineConfig

if TYPE_CHECKING:
    from memx.engine.postgres import PostgresEngine
    from memx.engine.sqlite import SQLiteEngine
