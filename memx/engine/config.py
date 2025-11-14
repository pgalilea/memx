from dataclasses import dataclass


@dataclass
class SQLEngineConfig:
    table: str
    add_query: int
    get_query: float
