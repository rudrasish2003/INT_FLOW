from fastapi import APIRouter
from .schemas import ChatRequest, ChatResponse
from .service import handle_chat, reset_session

router = APIRouter(prefix="/api/agent", tags=["HR Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return await handle_chat(req)


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    reset_session(session_id)
    return {"reset": True}