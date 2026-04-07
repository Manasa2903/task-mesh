"""Calendar tools — called by the Calendar Agent.

Uses the Google Calendar API via a service-account or OAuth token.
Falls back to storing events in Firestore when credentials are unavailable
(useful in development).
"""

from typing import Dict, List, Optional

from datetime import datetime, timedelta, timezone
from db.store import (
    create_calendar_event_doc,
    list_calendar_events_docs,
    write_log,
)
from utils.json_safety import make_json_safe

AGENT_NAME = "calendar_agent"

# ---------------------------------------------------------------------------
# Google Calendar API helpers
# ---------------------------------------------------------------------------

def _get_calendar_service():
    """Attempt to build a Google Calendar API service.

    Returns None when credentials are unavailable so the tool can
    fall back to Firestore-only mode.
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        from config import get_settings

        settings = get_settings()
        creds = service_account.Credentials.from_service_account_file(
            settings.google_application_credentials,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return build("calendar", "v3", credentials=creds)
    except Exception:
        return None


def _get_calendar_id() -> str:
    try:
        from config import get_settings
        return get_settings().google_calendar_id or "primary"
    except Exception:
        return "primary"


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def _with_default_end_time(start_time: str, end_time: Optional[str]) -> str:
    if end_time:
        return end_time
    try:
        start_dt = datetime.fromisoformat(start_time)
        return (start_dt + timedelta(hours=1)).isoformat()
    except ValueError:
        return start_time


async def _store_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str,
    attendees_list: List[str],
    source: str,
    calendar_error: str = "",
    extra: Optional[Dict] = None,
) -> Dict:
    data = {
        "title": title,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees_list,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }
    if calendar_error:
        data["calendar_error"] = calendar_error
    if extra:
        data.update(extra)
    return make_json_safe(await create_calendar_event_doc(data))


async def create_calendar_event(
    title: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: str = "",
    attendees: Optional[str] = None,
) -> Dict:
    """Create a calendar event.

    If Google Calendar credentials are available the event is created via
    the API; otherwise it is persisted in Firestore.

    Args:
        title: Event title / summary.
        start_time: ISO-8601 datetime string for the start.
        end_time: ISO-8601 datetime string for the end (defaults to +1 hour).
        description: Optional event description.
        attendees: Optional comma-separated list of email addresses.

    Returns:
        The created event record.
    """
    attendees_list = [a.strip() for a in attendees.split(",")] if attendees else []
    input_data = {
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "description": description,
        "attendees": attendees_list,
    }

    end_time = _with_default_end_time(start_time, end_time)

    try:
        service = _get_calendar_service()
        if service:
            body = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"},
            }
            if attendees_list:
                body["attendees"] = [{"email": e} for e in attendees_list]

            try:
                event = (
                    service.events()
                    .insert(calendarId=_get_calendar_id(), body=body)
                    .execute()
                )
                result = await _store_calendar_event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    attendees_list=attendees_list,
                    source="google_calendar",
                    extra={
                        "google_event_id": event["id"],
                        "link": event.get("htmlLink", ""),
                    },
                )
            except Exception as exc:
                result = await _store_calendar_event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    attendees_list=attendees_list,
                    source="app_db_calendar_fallback",
                    calendar_error=str(exc),
                )
        else:
            result = await _store_calendar_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                attendees_list=attendees_list,
                source="app_db",
            )

        await write_log(AGENT_NAME, "create_calendar_event", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "create_calendar_event", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def get_calendar_events(
    date: Optional[str] = None,
    max_results: int = 10,
) -> List[Dict]:
    """Retrieve upcoming calendar events.

    Args:
        date: Optional ISO-8601 date string to filter events for that day.
        max_results: Maximum number of events to return.

    Returns:
        List of event records.
    """
    input_data = {"date": date, "max_results": max_results}
    try:
        result = make_json_safe(
            await list_calendar_events_docs(date=date, limit=max_results)
        )
        service = _get_calendar_service()
        if service:
            list_kwargs = {
                "calendarId": _get_calendar_id(),
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            }
            if date:
                try:
                    date_part = date[:10]
                    day_start = datetime.fromisoformat(date_part).replace(
                        tzinfo=timezone.utc
                    )
                    day_end = day_start + timedelta(days=1)
                    list_kwargs["timeMin"] = day_start.isoformat().replace(
                        "+00:00", "Z"
                    )
                    list_kwargs["timeMax"] = day_end.isoformat().replace(
                        "+00:00", "Z"
                    )
                except ValueError:
                    list_kwargs["timeMin"] = datetime.now(timezone.utc).isoformat()
            else:
                list_kwargs["timeMin"] = datetime.now(timezone.utc).isoformat()

            try:
                events_result = (
                    service.events()
                    .list(**list_kwargs)
                    .execute()
                )
                items = events_result.get("items", [])
                google_events = make_json_safe([
                    {
                        "id": e["id"],
                        "title": e.get("summary", ""),
                        "start_time": e["start"].get(
                            "dateTime", e["start"].get("date")
                        ),
                        "end_time": e["end"].get("dateTime", e["end"].get("date")),
                        "source": "google_calendar",
                    }
                    for e in items
                ])

                seen_google_ids = {
                    event.get("google_event_id") or event.get("id")
                    for event in result
                    if event.get("google_event_id") or event.get("id")
                }
                seen_event_keys = {
                    (
                        event.get("title", ""),
                        event.get("start_time", ""),
                        event.get("end_time", ""),
                    )
                    for event in result
                }
                for event in google_events:
                    event_key = (
                        event.get("title", ""),
                        event.get("start_time", ""),
                        event.get("end_time", ""),
                    )
                    if (
                        event.get("id") in seen_google_ids
                        or event_key in seen_event_keys
                    ):
                        continue
                    result.append(event)
                    if len(result) >= max_results:
                        break
            except Exception:
                pass

        await write_log(
            AGENT_NAME, "get_calendar_events", input_data, {"count": len(result)}
        )
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "get_calendar_events", input_data, {},
            success=False, error_message=str(exc),
        )
        raise
