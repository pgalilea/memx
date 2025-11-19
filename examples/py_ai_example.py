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

    # it is your responsability to add the messages as a list[dict]
    messages = orjson.loads(result1.new_messages_json())

    await m1.add(messages)  # messages: list[dict] must be json serializable

    session_id = m1.get_id()
    print("Messages added with session_id: ", session_id)

    # resume the conversation from 'another' memory
    m2 = await engine.get_session(session_id)
    old_messages = ModelMessagesTypeAdapter.validate_python(await m2.get())  # type: ignore

    print("Past messages:\n", old_messages)

    result2 = await agent.run(
        "Could you tell me more about the authors?", message_history=old_messages
    )
    print("\n\nContext aware result:\n", result2.output)


if __name__ == "__main__":
    asyncio.run(main())
