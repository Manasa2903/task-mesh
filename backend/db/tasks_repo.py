"""Firestore helpers for tasks."""

from __future__ import annotations

from typing import Dict, List, Optional

from datetime import datetime, timezone
from google.cloud.firestore import AsyncClient
from db import get_firestore_client, TASKS_COLLECTION
from utils.json_safety import make_json_safe


async def create_task_doc(
    title: str,
    description: str = "",
    due_date: Optional[str] = None,
    priority: str = "medium",
    status: str = "pending",
) -> Dict:
    """Insert a new task document and return it with its ID."""
    db: AsyncClient = get_firestore_client()
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    _, doc_ref = await db.collection(TASKS_COLLECTION).add(data)
    return make_json_safe({"id": doc_ref.id, **data})


async def list_tasks_docs(
    status_filter: Optional[str] = None, limit: int = 50
) -> List[Dict]:
    """Return tasks, optionally filtered by status."""
    db: AsyncClient = get_firestore_client()
    query = db.collection(TASKS_COLLECTION).order_by(
        "created_at", direction="DESCENDING"
    ).limit(limit)
    if status_filter:
        query = query.where("status", "==", status_filter)
    docs = [doc async for doc in query.stream()]
    return make_json_safe([{"id": d.id, **d.to_dict()} for d in docs])


async def update_task_doc(task_id: str, updates: Dict) -> Optional[Dict]:
    """Update a task by ID. Returns updated doc or None if not found."""
    db: AsyncClient = get_firestore_client()
    ref = db.collection(TASKS_COLLECTION).document(task_id)
    snap = await ref.get()
    if not snap.exists:
        return None
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await ref.update(updates)
    snap = await ref.get()
    return make_json_safe({"id": snap.id, **snap.to_dict()})


async def delete_task_doc(task_id: str) -> bool:
    """Delete a task by ID. Returns True if it existed."""
    db: AsyncClient = get_firestore_client()
    ref = db.collection(TASKS_COLLECTION).document(task_id)
    snap = await ref.get()
    if not snap.exists:
        return False
    await ref.delete()
    return True
