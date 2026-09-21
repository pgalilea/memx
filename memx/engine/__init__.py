from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from memx.memory import BaseMemory


Eng = TypeVar("Eng", bound="BaseEngine")


class EngineSync(Generic[Eng]):
    """Blocking namespace bound to an engine instance."""

    pe: Eng

    def __init__(self, parent: Eng):
        self.pe = parent

    def get_session(self, id: str | UUID) -> BaseMemory | None:
        raise NotImplementedError


class BaseEngine(ABC):
    sync: EngineSync

    @abstractmethod
    def create_session(self) -> BaseMemory:
        """Create a memory session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> BaseMemory | None:
        """Get a memory session from backend."""
        pass
