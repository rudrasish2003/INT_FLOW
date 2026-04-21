from pydantic import BaseModel
from typing import Any, Optional, List, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    # one of: thinking | collecting | executing | done | error
    status: str
    workflow_result: Optional[Any] = None
    collected: Optional[dict] = None