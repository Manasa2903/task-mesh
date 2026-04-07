"""Execution logs route — view agent/tool execution history."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from db.store import list_logs

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def get_logs(session_id: Optional[str] = None, limit: int = 100):
    """Return execution logs, optionally filtered by session_id."""
    try:
        return await list_logs(session_id=session_id, limit=min(limit, 500))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
