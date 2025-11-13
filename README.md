<p align="center">
  <a href="https://github.com/pgalilea/memx"><img src="https://i.ibb.co/JjYq8fzW/memx.png" alt="memx - memory layer"></a>
</p>

<br/>
Lightweight and extensible memory layer for LLMs.
<br/><br/>

**Important Disclaimer**: This library is intended to be production-ready, but currently is in active development. Fix the version and run your own tests :)


##  🔥 Key Features
- **Framework agnostic**: Use your preferred AI agent framework.
- **Own infrastructure**: Use your preferred cloud provider. No third-party api keys; your data, your rules.
- **Multiple backends**: Move from your local *POC* to production deployment, seamlessly (SQLite, MongoDB, PostgreSQL).
- **Sync and async api**: Highly compatible with modern and *legacy* frameworks. 
- **No forced schema**: As long it is a list of json serializable objects.
- **Resumable memory**: Perfect for chat applications and REST APIs
- **Robust**: Get production-ready code with minimal effort.


## ⚙️ Installation

From pypi
```bash
pip install memx-lm
```
Or clone the repo and install it 
```bash
pip install . 
```

## 🚀 Quickstart

### OpenAI
Simple conversation with [OpenAI Python library](https://github.com/openai/openai-python)
```Python
# https://platform.openai.com/docs/guides/conversation-state?api-mode=responses
# tested on openai==2.6.1

from openai import OpenAI
from memx.memory.sqlite import SQLiteMemory

sqlite_uri = "sqlite+aiosqlite:///message-storage.db"
m1 = SQLiteMemory(sqlite_uri, "memx-messages")

client = OpenAI()

m1.sync.add([{"role": "user", "content": "tell me a good joke about programmers"}])

first_response = client.responses.create(
    model="gpt-4o-mini", input=m1.sync.get(), store=False
)

print(first_response.output_text)

m1.sync.add(
    [{"role": r.role, "content": r.content[0].text} for r in first_response.output]
)

m1.sync.add([{"role": "user", "content": "tell me another"}])

second_response = client.responses.create(
    model="gpt-4o-mini", input=m1.sync.get(), store=False
)

m1.sync.add(
    [{"role": r.role, "content": r.content[0].text} for r in second_response.output]
)

print(f"\n\n{second_response.output_text}")

print(m1.sync.get())
```
### Pydantic AI
Message history with async [Pydantic AI](https://ai.pydantic.dev/) + [Gemini](https://ai.google.dev/gemini-api/docs)
```Python
import asyncio
import os

import orjson
from memx.memory.sqlite import SQLiteMemory
from pydantic_ai import Agent, ModelMessagesTypeAdapter
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

# Reference: https://ai.pydantic.dev/message-history/

# Initialize the GoogleProvider for Vertex AI
PROJECT = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")

provider = GoogleProvider(
    vertexai=True, project=PROJECT, location=LOCATION
)

model = GoogleModel(
    model_name="gemini-2.0-flash",
    provider=provider,
)

agent = Agent(model)


async def main():
    sqlite_uri = "sqlite+aiosqlite:///message_store.db"
    m1 = SQLiteMemory(sqlite_uri, "my-messages")

    result1 = await agent.run('Where does "hello world" come from?')

    # it is your responsibility to add the messages as a list[dict]
    messages = orjson.loads(result1.new_messages_json())

    await m1.add(messages)  # messages: list[dict] must be json serializable

    session_id = m1.get_id()
    print("Messages added with session_id: ", session_id)

    # resume the conversation from 'another' memory
    m2 = SQLiteMemory(sqlite_uri, "my-messages", session_id=session_id)
    old_messages = ModelMessagesTypeAdapter.validate_python(await m2.get())

    print("Past messages:\n", old_messages)

    result2 = await agent.run(
        "Could you tell me more about the authors?", message_history=old_messages
    )
    print("\n\nContext aware result:\n", result2.output)


if __name__ == "__main__":
    asyncio.run(main())

```

You can change the memory backend with minimal modifications. Same api to add and get messages.
```Python
from memx.memory.mongodb import MongoDBMemory
from memx.memory.postgres import PostgresMemory
from memx.memory.sqlite import SQLiteMemory

# SQLite backend
sqlite_uri = "sqlite+aiosqlite:///message_store.db"
m1 = SQLiteMemory(sqlite_uri, "my-messages")

# PostgreSQL backend
pg_uri = "postgresql+psycopg://admin:1234@localhost:5433/test-database"
m2 = PostgresMemory(pg_uri, "memx-messages")

# MongoDB backend
mongodb_uri = "mongodb://admin:1234@localhost:27017"
m3 = MongoDBMemory(uri=mongodb_uri, database="memx-test", collection="memx-messages")

```

## Tasks
- [x] Add mongodb backend
- [x] Add SQLite backend
- [x] Add Postgres backend
- [ ] Add redis backend
- [ ] Add tests
- [ ] Publish on pypi
- [ ] Add full sync support
- [ ] Add docstrings