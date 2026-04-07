"""In-memory storage fallback when Firestore is unavailable.

Implements the same async interface as the Firestore repos so everything
works identically in development without GCP credentials.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from utils.json_safety import make_json_safe


class InMemoryCollection:
    """Simple dict-backed collection mirroring Firestore semantics."""

    def __init__(self) -> None:
        self._docs: Dict[str, Dict] = {}

    async def add(self, data: Dict) -> str:
        doc_id = uuid.uuid4().hex[:20]
        self._docs[doc_id] = make_json_safe({**data})
        return doc_id

    async def get(self, doc_id: str) -> Optional[Dict]:
        doc = self._docs.get(doc_id)
        if doc is None:
            return None
        return make_json_safe({"id": doc_id, **doc})

    async def update(self, doc_id: str, updates: Dict) -> Optional[Dict]:
        if doc_id not in self._docs:
            return None
        self._docs[doc_id].update(make_json_safe(updates))
        return make_json_safe({"id": doc_id, **self._docs[doc_id]})

    async def delete(self, doc_id: str) -> bool:
        if doc_id not in self._docs:
            return False
        del self._docs[doc_id]
        return True

    async def list_all(
        self,
        order_by: str = "created_at",
        direction: str = "DESCENDING",
        limit: int = 50,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        items = [{"id": k, **v} for k, v in self._docs.items()]
        if filters:
            for key, value in filters.items():
                items = [i for i in items if i.get(key) == value]
        reverse = direction == "DESCENDING"
        items.sort(key=lambda x: x.get(order_by, ""), reverse=reverse)
        return make_json_safe(items[:limit])


# Singleton collections
_tasks = InMemoryCollection()
_notes = InMemoryCollection()
_logs = InMemoryCollection()
_calendar_events = InMemoryCollection()
_chat_messages = InMemoryCollection()


# ── Tasks ─────────────────────────────────────────────────

async def create_task_doc(
    title: str,
    description: str = "",
    due_date: Optional[str] = None,
    priority: str = "medium",
    status: str = "pending",
) -> Dict:
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
    doc_id = await _tasks.add(data)
    return make_json_safe({"id": doc_id, **data})


async def list_tasks_docs(
    status_filter: Optional[str] = None, limit: int = 50
) -> List[Dict]:
    filters = {"status": status_filter} if status_filter else None
    return await _tasks.list_all(
        order_by="created_at", direction="DESCENDING", limit=limit, filters=filters,
    )


async def update_task_doc(task_id: str, updates: Dict) -> Optional[Dict]:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    return make_json_safe(await _tasks.update(task_id, updates))


async def delete_task_doc(task_id: str) -> bool:
    return await _tasks.delete(task_id)


# ── Notes ─────────────────────────────────────────────────

async def create_note_doc(
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
) -> Dict:
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }
    doc_id = await _notes.add(data)
    return make_json_safe({"id": doc_id, **data})


async def list_notes_docs(limit: int = 50) -> List[Dict]:
    return await _notes.list_all(
        order_by="created_at", direction="DESCENDING", limit=limit,
    )


async def get_note_doc(note_id: str) -> Optional[Dict]:
    return await _notes.get(note_id)


async def update_note_doc(note_id: str, updates: Dict) -> Optional[Dict]:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    return make_json_safe(await _notes.update(note_id, updates))


async def delete_note_doc(note_id: str) -> bool:
    return await _notes.delete(note_id)


# ── Logs ──────────────────────────────────────────────────

async def write_log(
    agent_name: str,
    tool_name: str,
    input_data: Dict,
    output_data: Dict,
    session_id: str = "",
    success: bool = True,
    error_message: str = "",
) -> Dict:
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
    doc_id = await _logs.add(data)
    return make_json_safe({"id": doc_id, **data})


async def list_logs(
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    filters = {"session_id": session_id} if session_id else None
    return await _logs.list_all(
        order_by="timestamp", direction="DESCENDING", limit=limit, filters=filters,
    )


# ── Calendar Events ──────────────────────────────────────

async def create_calendar_event_doc(data: Dict) -> Dict:
    doc_id = await _calendar_events.add(data)
    return make_json_safe({"id": doc_id, **data})


async def list_calendar_events_docs(
    date: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    events = await _calendar_events.list_all(
        order_by="start_time", limit=limit,
    )
    if date:
        events = [
            event for event in events
            if event.get("start_time", "").startswith(date)
        ]
    return events[:limit]


# ── Chat Messages ────────────────────────────────────────

async def add_chat_message(
    session_id: str,
    role: str,
    text: str,
    steps: Optional[List[Dict]] = None,
) -> Dict:
    data = {
        "session_id": session_id,
        "role": role,
        "text": text,
        "steps": make_json_safe(steps or []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    doc_id = await _chat_messages.add(data)
    return make_json_safe({"id": doc_id, **data})


async def list_chat_messages(
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    filters = {"session_id": session_id} if session_id else None
    return await _chat_messages.list_all(
        order_by="timestamp",
        direction="ASCENDING",
        limit=limit,
        filters=filters,
    )


async def clear_chat_messages(session_id: Optional[str] = None) -> Dict:
    if not session_id:
        deleted = len(_chat_messages._docs)
        _chat_messages._docs.clear()
        return {"deleted": deleted, "session_id": ""}

    deleted = 0
    for doc_id, doc in list(_chat_messages._docs.items()):
        if doc.get("session_id") == session_id:
            del _chat_messages._docs[doc_id]
            deleted += 1
    return {"deleted": deleted, "session_id": session_id}
