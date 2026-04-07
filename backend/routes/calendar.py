"""Calendar routes — direct event endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tools.calendar_tools import create_calendar_event, get_calendar_events

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CreateCalendarEventRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    start_time: str = Field(..., min_length=1)
    end_time: Optional[str] = None
    description: str = ""
    attendees: Optional[str] = None


@router.get("/events")
async def list_calendar_events(
    date: Optional[str] = None,
    max_results: int = 100,
):
    """List upcoming calendar events."""
    try:
        return await get_calendar_events(date=date, max_results=min(max_results, 100))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/events", status_code=201)
async def add_calendar_event(req: CreateCalendarEventRequest):
    """Create a calendar event."""
    try:
        return await create_calendar_event(
            title=req.title,
            start_time=req.start_time,
            end_time=req.end_time,
            description=req.description,
            attendees=req.attendees,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
