# /// script
# dependencies = [
#   "langgraph==1.2.11",
#   "memx-ai[sqlite]",
# ]
# ///


# https://docs.langchain.com/oss/python/langgraph/graph-api

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from memx.engine.sqlite import SQLiteEngine


engine = SQLiteEngine("sqlite+aiosqlite:///:memory:", "memx-messages", setup=True)
memory = engine.create_session()  # create a new session


class State(TypedDict):
    counter: int


def increment(state: State) -> State:
    # resume from memory: get_one returns the last stored state (or None)
    current = memory.sync.get_one()
    counter = (current["counter"] if current else 0) + 1  # type: ignore

    # persist the new state
    memory.sync.put({"counter": counter})

    return {"counter": counter}  # type: ignore


builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_edge(START, "increment")
builder.add_edge("increment", END)

graph = builder.compile()

for _ in range(3):
    result = graph.invoke({"counter": 0})
    print(result)

print("Persisted state:", memory.sync.get_one())
