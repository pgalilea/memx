from abc import ABC, abstractmethod


class BaseMemory(ABC):
    @abstractmethod
    def add(self, messages: list[dict]):
        pass

    @abstractmethod
    def get(self) -> list[str]:
        pass

    def get_id(self) -> str:
        return self._session_id
