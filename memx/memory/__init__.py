from abc import ABC, abstractmethod

from memx.utils import JSON


class BaseMemory(ABC):
    @abstractmethod
    def add(self, messages: list[JSON]):
        pass

    @abstractmethod
    def get(self) -> list[JSON]:
        pass

    def get_id(self) -> str:
        return self._session_id  # type: ignore
