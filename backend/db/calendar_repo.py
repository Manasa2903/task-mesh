"""Firestore helpers for calendar events."""

from __future__ import annotations

from typing import Dict, List, Optional

from google.cloud.firestore import AsyncClient
from db import CALENDAR_EVENTS_COLLECTION, get_firestore_client
from utils.json_safety import make_json_safe


async def create_calendar_event_doc(data: Dict) -> Dict:
    """Insert a calendar event document and return it with its ID."""
    db: AsyncClient = get_firestore_client()
    _, doc_ref = await db.collection(CALENDAR_EVENTS_COLLECTION).add(data)
    return make_json_safe({"id": doc_ref.id, **data})


async def list_calendar_events_docs(
    date: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    """Return calendar events ordered by start time."""
    db: AsyncClient = get_firestore_client()
    query = db.collection(CALENDAR_EVENTS_COLLECTION).order_by("start_time").limit(
        limit
    )
    docs = [doc async for doc in query.stream()]
    events = make_json_safe([{"id": d.id, **d.to_dict()} for d in docs])
    if date:
        events = [
            event for event in events
            if event.get("start_time", "").startswith(date)
        ]
    return events[:limit]
