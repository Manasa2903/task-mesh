"""Firestore helpers for chat history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from google.cloud.firestore import AsyncClient
from db import CHAT_MESSAGES_COLLECTION, get_firestore_client
from utils.json_safety import make_json_safe


async def add_chat_message(
    session_id: str,
    role: str,
    text: str,
    steps: Optional[List[Dict]] = None,
) -> Dict:
    """Insert a chat message."""
    db: AsyncClient = get_firestore_client()
    data = {
        "session_id": session_id,
        "role": role,
        "text": text,
        "steps": make_json_safe(steps or []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _, doc_ref = await db.collection(CHAT_MESSAGES_COLLECTION).add(data)
    return make_json_safe({"id": doc_ref.id, **data})


async def list_chat_messages(
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Return chat messages ordered by timestamp."""
    db: AsyncClient = get_firestore_client()
    query = db.collection(CHAT_MESSAGES_COLLECTION).order_by("timestamp").limit(
        limit
    )
    docs = [doc async for doc in query.stream()]
    messages = make_json_safe([{"id": d.id, **d.to_dict()} for d in docs])
    if session_id:
        messages = [
            message for message in messages
            if message.get("session_id") == session_id
        ]
    return messages


async def clear_chat_messages(session_id: Optional[str] = None) -> Dict:
    """Delete chat messages, optionally scoped to one session."""
    db: AsyncClient = get_firestore_client()
    query = db.collection(CHAT_MESSAGES_COLLECTION)
    if session_id:
        query = query.where("session_id", "==", session_id)
    docs = [doc async for doc in query.stream()]
    for doc in docs:
        await doc.reference.delete()
    return {"deleted": len(docs), "session_id": session_id or ""}
