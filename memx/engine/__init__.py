from abc import ABC, abstractmethod

from memx.memory import BaseMemory


class BaseEngine(ABC):
    @abstractmethod
    def get_session(self, session_id: str = None) -> BaseMemory:
        pass
