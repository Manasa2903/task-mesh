"""Chat service — runs the orchestrator agent via Google ADK's Runner."""

from __future__ import annotations

import inspect
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import uuid
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agents.orchestrator import orchestrator_agent
from db.store import add_chat_message
from tools.calendar_tools import create_calendar_event, get_calendar_events
from tools.task_tools import create_task
from utils.json_safety import make_json_safe

# ADK session management


def _sanitize_event(event):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_response:
                part.function_response.response = make_json_safe(
                    part.function_response.response
                )
            if part.function_call and part.function_call.args:
                part.function_call.args = make_json_safe(part.function_call.args)
    if event.actions and event.actions.state_delta:
        event.actions.state_delta = make_json_safe(event.actions.state_delta)
    return event


class JsonSafeInMemorySessionService(InMemorySessionService):
    def append_event(self, session, event):
        return super().append_event(session=session, event=_sanitize_event(event))


_session_service = JsonSafeInMemorySessionService()

# ADK Runner wraps agent execution
_runner = Runner(
    agent=orchestrator_agent,
    app_name="task_mesh",
    session_service=_session_service,
)

LOCAL_TZ = ZoneInfo("Asia/Kolkata")
MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


async def _resolve(value):
    """Return awaited values while supporting sync ADK service methods."""
    if inspect.isawaitable(value):
        return await value
    return value


def _unwrap_tool_response(response: Any) -> Any:
    response = make_json_safe(response)
    if isinstance(response, dict) and "result" in response:
        return response["result"]
    return response


def _fallback_response_from_tool(tool_name: str, response: Any) -> str:
    if tool_name == "transfer_to_agent":
        return (
            "I routed the request, but the scheduling tool did not run. "
            "Please try again after restarting the backend."
        )

    data = _unwrap_tool_response(response)
    if tool_name == "create_calendar_event" and isinstance(data, dict):
        title = data.get("title", "the event")
        start_time = _format_datetime(data.get("start_time", "the requested time"))
        end_time = data.get("end_time")
        source = data.get("source", "")
        location_note = ""
        if source == "google_calendar":
            location_note = " Synced to Google Calendar."
        elif source == "app_db_calendar_fallback":
            location_note = (
                " Google Calendar sync failed; saved in TaskMesh Calendar."
            )
        elif source:
            location_note = " Saved in TaskMesh Calendar."
        if end_time:
            return (
                f"Scheduled {title} from {start_time} to "
                f"{_format_datetime(end_time)}.{location_note}"
            )
        return f"Scheduled {title} for {start_time}.{location_note}"

    if tool_name == "create_task" and isinstance(data, dict):
        due_date = data.get("due_date")
        if due_date:
            return f"Created task: {data.get('title', 'Untitled task')} for {_format_datetime(due_date)}."
        return f"Created task: {data.get('title', 'Untitled task')}."

    if tool_name == "save_note" and isinstance(data, dict):
        return f"Saved note: {data.get('title', 'Untitled note')}."

    if tool_name.startswith("get_") and isinstance(data, list):
        return f"Found {len(data)} result(s)."

    return "I completed the requested action, but did not get a final summary from the model."


def _fallback_response_from_tools(tool_responses: List[Dict[str, Any]]) -> str:
    summaries: List[str] = []
    for tool_response in tool_responses:
        tool_name = tool_response["tool"]
        if tool_name.startswith("get_"):
            continue
        summaries.append(
            _fallback_response_from_tool(tool_name, tool_response["response"])
        )
    if summaries:
        return " ".join(summaries)
    return _fallback_response_from_tool(
        tool_responses[-1]["tool"], tool_responses[-1]["response"]
    )


def _format_datetime(value: Any) -> str:
    if not value:
        return ""
    if not isinstance(value, str):
        return str(value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo:
        parsed = parsed.astimezone(LOCAL_TZ)
    if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
        return parsed.strftime("%d %b %Y")
    return parsed.strftime("%d %b %Y, %H:%M")


def _parse_requested_datetime(message: str) -> Optional[datetime]:
    text = message.lower()
    match = re.search(r"\b(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    meridiem = match.group(3)
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    now = datetime.now(LOCAL_TZ)
    if "day after tomorrow" in text:
        target_date = now.date() + timedelta(days=2)
    elif "tomorrow" in text:
        target_date = now.date() + timedelta(days=1)
    else:
        target_date = now.date()
        if (hour, minute) <= (now.hour, now.minute):
            target_date = target_date + timedelta(days=1)

    return datetime.combine(target_date, datetime.min.time(), LOCAL_TZ).replace(
        hour=hour, minute=minute
    )


def _parse_requested_date(message: str) -> Optional[datetime]:
    text = message.lower()
    now = datetime.now(LOCAL_TZ)
    if "day after tomorrow" in text:
        target_date = now.date() + timedelta(days=2)
        return datetime.combine(target_date, datetime.min.time(), LOCAL_TZ)
    if "tomorrow" in text:
        target_date = now.date() + timedelta(days=1)
        return datetime.combine(target_date, datetime.min.time(), LOCAL_TZ)
    if "today" in text:
        return datetime.combine(now.date(), datetime.min.time(), LOCAL_TZ)

    match = re.search(
        r"\b(?:by|on|due)\s+(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)\b",
        message,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    day = int(match.group(1))
    month = MONTHS.get(match.group(2).lower())
    if not month:
        return None
    year = now.year
    target = datetime(year, month, day, tzinfo=LOCAL_TZ)
    if target.date() < now.date():
        target = target.replace(year=year + 1)
    return target


def _title_case(value: str) -> str:
    value = value.strip(" .")
    if not value:
        return value
    return value[:1].upper() + value[1:]


def _extract_task_title(message: str) -> str:
    match = re.search(r"\bfor\s+(.+)$", message, flags=re.IGNORECASE)
    if match:
        return _title_case(match.group(1))
    cleaned = re.sub(
        r"^create\s+(a\s+)?task\s*", "", message, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"^to\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b(by|on|due)\s+\d{1,2}(st|nd|rd|th)?\s+[a-zA-Z]+\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\b(at\s*)?\d{1,2}(:\d{2})?\s*(am|pm)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\btomorrow\b|\btoday\b", "", cleaned, flags=re.IGNORECASE)
    return _title_case(cleaned) or "Task"


def _extract_event_title(message: str) -> str:
    match = re.search(
        r"schedule\s+(?:a\s+|an\s+|the\s+)?(.+?)(?:\s+tomorrow|\s+today|\s+at\s+\d|$)",
        message,
        flags=re.IGNORECASE,
    )
    if not match:
        return "Meeting"
    title = re.sub(r"\band\s+remind\s+me\s+to.*$", "", match.group(1), flags=re.IGNORECASE)
    return _title_case(title) or "Meeting"


def _extract_reminder_title(message: str) -> Optional[str]:
    match = re.search(r"\bremind\s+me\s+to\s+(.+)$", message, flags=re.IGNORECASE)
    if not match:
        return None
    return _title_case(match.group(1))


def _overlaps(start: datetime, end: datetime, event: Dict[str, Any]) -> bool:
    try:
        event_start = datetime.fromisoformat(event["start_time"])
        event_end = datetime.fromisoformat(event["end_time"])
    except Exception:
        return False
    return start < event_end and end > event_start


async def _next_available_start(start: datetime) -> tuple[datetime, bool]:
    date_key = start.date().isoformat()
    events = await get_calendar_events(date=date_key, max_results=50)
    candidate = start
    for _ in range(24):
        candidate_end = candidate + timedelta(hours=1)
        if not any(_overlaps(candidate, candidate_end, event) for event in events):
            return candidate, candidate != start
        candidate += timedelta(minutes=30)
    return start, False


async def _try_handle_direct_intent(message: str) -> Optional[Dict[str, Any]]:
    text = message.lower()
    requested_dt = _parse_requested_datetime(message)
    requested_date = requested_dt or _parse_requested_date(message)

    if re.search(r"\bcreate\s+(a\s+)?task\b", text) and requested_date:
        title = _extract_task_title(message)
        task = await create_task(title=title, due_date=requested_date.isoformat())
        return {
            "response": _fallback_response_from_tool("create_task", task),
            "steps": [{
                "agent": "orchestrator",
                "tool": "create_task",
                "args": {"title": title, "due_date": requested_date.isoformat()},
            }],
        }

    if not requested_dt:
        return None

    if "schedule" in text and any(
        word in text
        for word in ("meeting", "event", "appointment", "call", "haircut", "hair cut")
    ):
        start = requested_dt
        start, adjusted = await _next_available_start(start)
        end = start + timedelta(hours=1)
        title = _extract_event_title(message)
        event = await create_calendar_event(
            title=title,
            start_time=start.isoformat(),
            end_time=end.isoformat(),
        )
        steps = [{
            "agent": "orchestrator",
            "tool": "create_calendar_event",
            "args": {
                "title": title,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        }]
        tool_responses = [{"tool": "create_calendar_event", "response": event}]

        reminder_title = _extract_reminder_title(message)
        if reminder_title:
            reminder = await create_task(
                title=reminder_title,
                due_date=start.isoformat(),
            )
            steps.append({
                "agent": "orchestrator",
                "tool": "create_task",
                "args": {
                    "title": reminder_title,
                    "due_date": start.isoformat(),
                },
            })
            tool_responses.append({"tool": "create_task", "response": reminder})

        response = _fallback_response_from_tools(tool_responses)
        if adjusted:
            response = (
                "The requested slot was busy, so I scheduled the next available "
                f"slot. {response}"
            )
        return {
            "response": response,
            "steps": steps,
        }

    return None


async def handle_chat(
    message: str,
    session_id: Optional[str] = None,
    user_id: str = "default_user",
) -> Dict:
    """Send a user message through the orchestrator and collect the response.

    Args:
        message: The user's natural-language message.
        session_id: Optional existing session ID for context continuity.
        user_id: Identifier for the user.

    Returns:
        dict with 'session_id', 'response' text, and 'steps' trace.
    """
    # Ensure a session exists
    if not session_id:
        session_id = str(uuid.uuid4())

    # Collect events from the runner
    response_text = ""
    tool_responses: List[Dict[str, Any]] = []
    steps: List[Dict] = []

    try:
        direct_result = await _try_handle_direct_intent(message)
        if direct_result:
            response_text = direct_result["response"]
            steps = make_json_safe(direct_result["steps"])
        else:
            session = await _resolve(
                _session_service.get_session(
                    app_name="task_mesh", user_id=user_id, session_id=session_id,
                )
            )
            if session is None:
                await _resolve(
                    _session_service.create_session(
                        app_name="task_mesh", user_id=user_id, session_id=session_id,
                    )
                )

            # Build ADK content message
            user_content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=message)],
            )

            async for event in _runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content,
            ):
                # Capture tool-call events for the execution trace
                function_calls = event.get_function_calls()
                if function_calls:
                    for fc in function_calls:
                        steps.append({
                            "agent": event.author or "orchestrator",
                            "tool": fc.name if fc.name else "unknown",
                            "args": make_json_safe(dict(fc.args) if fc.args else {}),
                        })

                function_responses = event.get_function_responses()
                if function_responses:
                    for fr in function_responses:
                        tool_responses.append({
                            "tool": fr.name if fr.name else "unknown",
                            "response": make_json_safe(fr.response),
                        })

                # Capture final text response
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = "\n".join(
                            p.text for p in event.content.parts if p.text
                        )
            if not response_text and tool_responses:
                response_text = _fallback_response_from_tools(tool_responses)
            elif not response_text:
                response_text = (
                    "I couldn't complete that request. Please try again with a little "
                    "more detail."
                )
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            response_text = (
                "The Gemini API rate limit has been reached. "
                "Please wait a minute and try again."
            )
        elif (
            "nodename nor servname provided" in error_msg
            or "Failed to establish a new connection" in error_msg
        ):
            response_text = (
                "I couldn't reach the Gemini API. Check your internet connection "
                "and API configuration, then try again."
            )
        else:
            response_text = f"An error occurred: {error_msg}"

    result = {
        "session_id": session_id,
        "response": response_text,
        "steps": make_json_safe(steps),
    }
    try:
        await add_chat_message(session_id=session_id, role="user", text=message)
        await add_chat_message(
            session_id=session_id,
            role="assistant",
            text=response_text,
            steps=result["steps"],
        )
    except Exception:
        pass
    return result
