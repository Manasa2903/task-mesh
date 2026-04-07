"""Firestore helpers for notes."""

from __future__ import annotations

from typing import Dict, List, Optional

from datetime import datetime, timezone
from google.cloud.firestore import AsyncClient
from db import get_firestore_client, NOTES_COLLECTION
from utils.json_safety import make_json_safe


async def create_note_doc(
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
) -> Dict:
    """Insert a new note document."""
    db: AsyncClient = get_firestore_client()
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }
    _, doc_ref = await db.collection(NOTES_COLLECTION).add(data)
    return make_json_safe({"id": doc_ref.id, **data})


async def list_notes_docs(limit: int = 50) -> List[Dict]:
    """Return all notes ordered by creation time."""
    db: AsyncClient = get_firestore_client()
    query = db.collection(NOTES_COLLECTION).order_by(
        "created_at", direction="DESCENDING"
    ).limit(limit)
    docs = [doc async for doc in query.stream()]
    return make_json_safe([{"id": d.id, **d.to_dict()} for d in docs])


async def get_note_doc(note_id: str) -> Optional[Dict]:
    """Get a single note by ID."""
    db: AsyncClient = get_firestore_client()
    ref = db.collection(NOTES_COLLECTION).document(note_id)
    snap = await ref.get()
    if not snap.exists:
        return None
    return make_json_safe({"id": snap.id, **snap.to_dict()})


async def update_note_doc(note_id: str, updates: Dict) -> Optional[Dict]:
    """Update a note by ID."""
    db: AsyncClient = get_firestore_client()
    ref = db.collection(NOTES_COLLECTION).document(note_id)
    snap = await ref.get()
    if not snap.exists:
        return None
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await ref.update(updates)
    snap = await ref.get()
    return make_json_safe({"id": snap.id, **snap.to_dict()})


async def delete_note_doc(note_id: str) -> bool:
    """Delete a note by ID."""
    db: AsyncClient = get_firestore_client()
    ref = db.collection(NOTES_COLLECTION).document(note_id)
    snap = await ref.get()
    if not snap.exists:
        return False
    await ref.delete()
    return True
