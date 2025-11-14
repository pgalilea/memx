from abc import ABC, abstractmethod

from memx.memory import BaseMemory


class BaseEngine(ABC):
    @abstractmethod
    def create_session(self) -> BaseMemory:
        """Create a memory session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> BaseMemory | None:
        """Get a memory session from backend."""
        pass
