from abc import ABC, abstractmethod

from memx.models import JSON


class BaseMemory(ABC):
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
