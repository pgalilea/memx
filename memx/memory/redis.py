from memx.memory import BaseMemory


class RedisMemory(BaseMemory):
    def __init__(self, uri: str):
        raise NotImplementedError("RedisMemory is not implemented yet")

    def add(self, messages: list[dict]):
        pass

    def get(self) -> list[dict]:
        pass
