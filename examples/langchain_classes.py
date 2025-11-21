# https://docs.langchain.com/oss/python/langchain/messages

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages import messages_from_dict

from memx.engine.sqlite import SQLiteEngine

model = init_chat_model("gpt-4o-mini")

engine = SQLiteEngine("sqlite+aiosqlite:///:memory:", "memx-messages", start_up=True)
m1 = engine.create_session()  # create a new session

# first interaction
messages = [
    SystemMessage("You are a helpful assistant."),
    HumanMessage("Hello, how are you?"),
    AIMessage("Hello!, how can I assist you today?"),
]

messages.append(HumanMessage("Tell me a joke about programmers, talking like a pirate"))
m1.sync.add([msg.model_dump(mode="json") for msg in messages])
response = model.invoke(messages)  # Returns AIMessage
print("First response:\n", response)
m1.sync.add([response.model_dump(mode="json")])

# a few hours later...
m2 = engine.sync.get_session(m1.get_id())  # resume the session later
message_history = messages_from_dict(
    [{"type": d["type"], "data": d} for d in m2.sync.get()]  # type: ignore
)  # get previous messages

new_msg = HumanMessage("Good one! any other jokes?")
m2.sync.add([new_msg.model_dump(mode="json")])  # type: ignore
message_history.append(new_msg)

response = model.invoke(message_history)  # Returns AIMessage
print("Second response:\n", response)
m2.sync.add([response.model_dump(mode="json")])  # type: ignore
m2.sync.get()  # type: ignore
