<p align="center">
  <a href="https://github.com/pgalilea/memx"><img src="https://i.ibb.co/zWg5V867/memx.png" alt="memx - memory layer"></a>
</p>

<br/>
<p align="center">Lightweight and extensible memory layer for LLMs.</p>
<br/><br/>

**Important Disclaimer**: This library is intended to be production-ready, but currently is in active development. Fix the package version and run your own tests :)


##  🔥 Key Features
- **Framework agnostic**: Use your preferred AI agent framework.
- **No vendor lock-in**: Use your preferred cloud provider or infrastructure. No third-party api keys; your data, your rules.
- **Multiple backends**: Seamlessly move from your local *POC* to production deployment (SQLite, MongoDB, PostgreSQL).
- **Sync and async api**: Highly compatible with modern and *legacy* frameworks. 
- **No forced schema**: As long it is a list of json serializable objects.
- **Resumable memory**: Perfect for chat applications and REST APIs.
- **Robust**: Get production-ready code with minimal effort.
- **No esoteric patching**: <abbr title="What you see is what you get">WYSIWYG</abbr>. Act as a sidecar for your framework without touching your libraries under the hood.


## ⚙️ Installation

From pypi:
```bash
pip install memx-ai
```

## 🚀 Quickstart

### OpenAI
Simple conversation using [OpenAI Python library](https://github.com/openai/openai-python)
```Python
# https://platform.openai.com/docs/guides/conversation-state?api-mode=responses
# tested on openai==2.6.1

from openai import OpenAI
from memx.engine.sqlite import SQLiteEngine

sqlite_uri = "sqlite+aiosqlite:///message-storage.db"
engine = SQLiteEngine(sqlite_uri, "memx-messages", start_up=True)
m1 = engine.create_session()  # create a new session

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
Message history with async [Pydantic AI](https://ai.pydantic.dev/) + OpenAI

```Python
# Reference: https://ai.pydantic.dev/message-history/

import asyncio

import orjson
from pydantic_ai import Agent, ModelMessagesTypeAdapter

from memx.engine.sqlite import SQLiteEngine

agent = Agent("openai:gpt-4o-mini")


async def main():
    sqlite_uri = "sqlite+aiosqlite:///message_store.db"
    engine = SQLiteEngine(sqlite_uri, "memx-messages", start_up=True)
    m1 = engine.create_session()  # create a new session

    result1 = await agent.run('Where does "hello world" come from?')

    # it is your responsibility to add the messages as a list[dict]
    messages = orjson.loads(result1.new_messages_json())

    await m1.add(messages)  # messages: list[dict] must be json serializable

    session_id = m1.get_id()
    print("Messages added with session_id: ", session_id)

    # resume the conversation from 'another' memory
    m2 = await engine.get_session(session_id)
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
from memx.engine.mongodb import MongoDBEngine
from memx.engine.postgres import PostgresEngine
from memx.engine.sqlite import SQLiteEngine

# SQLite backend
sqlite_uri = "sqlite+aiosqlite:///message_store.db"
e1 = SQLiteEngine(sqlite_uri, "memx-messages", start_up=True)
m1 = e1.create_session() # memory session ready to go

# PostgreSQL backend
pg_uri = "postgresql+psycopg://admin:1234@localhost:5433/test-database"
e2 = PostgresEngine(pg_uri, "memx-messages", start_up=True)
m2 = e2.create_session()

# MongoDB backend
mongodb_uri = "mongodb://admin:1234@localhost:27017"
e3 = MongoDBEngine(mongodb_uri, "memx-test", "memx-messages")
m3 = e3.create_session()

```

[More examples...](examples/)

## Tests
```sh
pytest tests -vs
```

## Tasks
- [x] Add mongodb backend
- [x] Add SQLite backend
- [x] Add Postgres backend
- [x] Add redis backend
- [ ] Add tests
- [x] Publish on pypi
- [x] Add full sync support
- [ ] Add docstrings