from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from memx.models import JSON


Mem = TypeVar("Mem", bound="BaseMemory")


class MemorySync(Generic[Mem]):
    """Blocking namespace bound to a memory instance."""

    pm: Mem

    def __init__(self, parent: Mem):
        self.pm = parent

    def add(self, messages: list[JSON]):
        raise NotImplementedError

    def get(self) -> list[JSON]:
        raise NotImplementedError

    def put(self, data: dict):
        self.add([data])

    def get_one(self) -> JSON | None:
        messages = self.get()

        return messages[-1] if messages else None


class BaseMemory(ABC):
    sync: MemorySync

    @abstractmethod
    def add(self, messages: list[JSON]):
        """Add messages to the memory."""
        pass

    @abstractmethod
    def get(self) -> list[JSON]:
        """Get messages from the memory."""
        pass

    def get_id(self) -> str:
        """Get the session id."""
        return self._session_id  # type: ignore
