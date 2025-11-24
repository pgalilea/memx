from dataclasses import dataclass


@dataclass(frozen=True)
class SQLEngineConfig:
    table: str
    add_query: int
    get_query: float
