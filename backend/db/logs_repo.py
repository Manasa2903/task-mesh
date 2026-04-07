"""Firestore helpers for execution logs."""

from __future__ import annotations

from typing import Dict, List, Optional

from datetime import datetime, timezone
from google.cloud.firestore import AsyncClient
from db import get_firestore_client, LOGS_COLLECTION
from utils.json_safety import make_json_safe


async def write_log(
    agent_name: str,
    tool_name: str,
    input_data: dict,
    output_data: dict,
    session_id: str = "",
    success: bool = True,
    error_message: str = "",
) -> dict:
    """Write an execution log entry to Firestore."""
    db: AsyncClient = get_firestore_client()
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "agent_name": agent_name,
        "tool_name": tool_name,
        "input": make_json_safe(input_data),
        "output": make_json_safe(output_data),
        "session_id": session_id,
        "success": success,
        "error_message": str(error_message),
        "timestamp": now,
    }
    _, doc_ref = await db.collection(LOGS_COLLECTION).add(data)
    return make_json_safe({"id": doc_ref.id, **data})


async def list_logs(
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Return execution logs, optionally filtered by session."""
    db: AsyncClient = get_firestore_client()
    query = db.collection(LOGS_COLLECTION).order_by(
        "timestamp", direction="DESCENDING"
    ).limit(limit)
    if session_id:
        query = query.where("session_id", "==", session_id)
    docs = [doc async for doc in query.stream()]
    return make_json_safe([{"id": d.id, **d.to_dict()} for d in docs])
