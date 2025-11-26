# https://docs.langchain.com/oss/python/langchain/messages#dictionary-format

# First interaction: POST /chat {"message":"tell me a joke about pirates"}
# Subsequent interactions: POST /chat/{chat_id} {"message":"another one!"}

from os import getenv
from uuid import UUID

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from langchain.chat_models import init_chat_model
from pydantic import BaseModel

from memx.engine.postgres import PostgresEngine

pg_uri = getenv("POSTGRES_URI")
engine = PostgresEngine(pg_uri, "memx-messages", start_up=True)
model = init_chat_model("gpt-4o-mini")

app = FastAPI(title="Chat API", version="1.0.0")


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    session_id: str | None = None


@app.post("/chat", response_model=ChatResponse)
def chat(message: ChatMessage):
    """
    Send a chat message without a specific session UUID.
    """
    session = engine.create_session()

    response = model.invoke([{"role": "user", "content": message.message}])

    session.sync.add(
        [
            {"role": "user", "content": message.message},
            {"role": "assistant", "content": response.content},
        ]
    )

    return ChatResponse(
        message=response.content,
        session_id=session.get_id(),
    )


@app.post("/chat/{chat_id}", response_model=ChatResponse)
def chat_with_uuid(chat_id: UUID, message: ChatMessage):
    """
    Send a chat message to a specific session identified by UUID.
    """

    # NOTE: its developer's responsability to check the user-session permissions
    session = engine.sync.get_session(chat_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    prev_messages = session.sync.get()
    user_message = [{"role": "user", "content": message.message}]

    response = model.invoke(prev_messages + user_message)

    session.sync.add(user_message + [{"role": "assistant", "content": response.content}])

    return ChatResponse(
        message=response.content,
        session_id=str(chat_id),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
