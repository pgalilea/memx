import asyncio
import pickle
from pathlib import Path
from uuid import uuid4

import aiofiles

from memx.memory import BaseMemory


class DiskMemory(BaseMemory):
    def __init__(self, session_id: str = None, dir: str = None):
        file_id = session_id if session_id else str(uuid4())
        file_dir = Path(dir) if dir else Path.home() / ".memx"

        self.file_path = Path(file_dir) / f"{file_id}.pkl"
        file_dir.mkdir(parents=True, exist_ok=True)

        if not self.file_path.is_file():
            with open(self.file_path, "wb") as f:
                pickle.dump([], f, protocol=pickle.HIGHEST_PROTOCOL)

        self._session_id = file_id

        self.sync = _sync(self)  # to group sync methods

    async def add(self, messages: list[dict]):
        # read the file
        async with aiofiles.open(self.file_path, "rb") as f:
            pickled_data = await f.read()

        stored_messages: list[dict] = await asyncio.to_thread(
            pickle.loads, pickled_data
        )

        # extend the messages
        stored_messages.extend(messages)

        # write the file
        pickled_data = await asyncio.to_thread(
            pickle.dumps, stored_messages, protocol=pickle.HIGHEST_PROTOCOL
        )

        async with aiofiles.open(self.file_path, "wb") as f:
            await f.write(pickled_data)

    async def get(self) -> list[dict]:
        async with aiofiles.open(self.file_path, "rb") as f:
            pickled_data = await f.read()

        stored_messages: list[dict] = await asyncio.to_thread(
            pickle.loads, pickled_data
        )

        return stored_messages


class _sync(BaseMemory):
    def __init__(self, parent: "DiskMemory"):
        self.pm = parent  # parent memory (?)

    def add(self, messages: list[dict]):
        with open(self.pm.file_path, "rb") as f:
            stored_messages: list[dict] = pickle.load(f)

        stored_messages.extend(messages)

        with open(self.pm.file_path, "wb") as f:
            pickle.dump(stored_messages, f, protocol=pickle.HIGHEST_PROTOCOL)

    def get(self) -> list[dict]:
        with open(self.pm.file_path, "rb") as f:
            stored_messages: list[dict] = pickle.load(f)

        return stored_messages


class InMemory(BaseMemory):
    # TODO: add .sync just for consistency
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
