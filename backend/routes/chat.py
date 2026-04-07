"""Chat route — main AI interaction endpoint."""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from db.store import clear_chat_messages, list_chat_messages
from services.chat_service import handle_chat

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


class StepTrace(BaseModel):
    agent: str
    tool: str
    args: dict


class ChatResponse(BaseModel):
    session_id: str
    response: str
    steps: List[StepTrace]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Process a user message through the multi-agent orchestrator."""
    result = await handle_chat(message=req.message, session_id=req.session_id)
    return ChatResponse(**result)


@router.get("/chat/history")
async def chat_history(session_id: Optional[str] = None, limit: int = 100):
    """Return saved chat messages."""
    return await list_chat_messages(session_id=session_id, limit=min(limit, 500))


@router.delete("/chat/history")
async def clear_chat_history(session_id: Optional[str] = None):
    """Clear saved chat messages."""
    return await clear_chat_messages(session_id=session_id)
