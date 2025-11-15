from memx.engine import BaseEngine
from memx.memory.redis import RedisMemory


class RedisEngine(BaseEngine):
    def __init__(self, uri: str):
        raise NotImplementedError("RedisEngine is not implemented yet")
        pass

    def create_session(self) -> RedisMemory:
        pass

    def get_session(self, session_id: str) -> RedisMemory | None:
        pass
