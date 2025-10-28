import pickle
from pathlib import Path
from uuid import uuid4

from memx.memory import BaseMemory


class DiskMemory(BaseMemory):
    def __init__(self, session_id: str = None, dir: str = None):
        file_id = session_id if session_id else str(uuid4())
        file_dir = dir if dir else Path.home() / ".memx"

        self.file_path = file_dir / f"{file_id}.pkl"
        file_dir.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "wb") as f:
            pickle.dump([], f, protocol=pickle.HIGHEST_PROTOCOL)

        self._session_id = file_id

    def add(self, messages: list[dict]):
        with open(self.file_path, "rb") as f:
            stored_messages: list[dict] = pickle.load(f)

        stored_messages.extend(messages)

        with open(self.file_path, "wb") as f:
            pickle.dump(stored_messages, f, protocol=pickle.HIGHEST_PROTOCOL)

    def get(self) -> list[dict]:
        with open(self.file_path, "rb") as f:
            stored_messages: list[dict] = pickle.load(f)

        return stored_messages


class InMemory(BaseMemory):
    def __init__(self, session_id: str = None):
        global __memx_in_memory__
        if "__memx_in_memory__" not in globals().keys():
            __memx_in_memory__ = {}

        if session_id:
            self._messages = __memx_in_memory__[session_id]
            _session_id = session_id
        else:
            _session_id = str(uuid4())
            __memx_in_memory__[_session_id] = []
            self._messages = __memx_in_memory__[_session_id]

        self._session_id = _session_id

    def add(self, messages: list[dict]):
        self._messages.extend(messages)

    def get(
        self,
    ) -> list[str]:
        return self._messages
