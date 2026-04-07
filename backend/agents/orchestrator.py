"""Orchestrator agent — coordinates task, calendar, and notes tools."""

from datetime import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from tools.calendar_tools import create_calendar_event, get_calendar_events
from tools.notes_tools import delete_note, get_note, get_notes, save_note, update_note
from tools.task_tools import create_task, delete_task, get_tasks, update_task
from utils.json_safety import make_json_safe


def _get_user_text(tool_context) -> str:
    user_content = tool_context._invocation_context.user_content
    if not user_content or not user_content.parts:
        return ""
    return " ".join(part.text or "" for part in user_content.parts).lower()


def _before_tool_callback(tool, args, tool_context):
    if tool.name != "create_task":
        return None

    title = str(args.get("title", "")).lower()
    user_text = _get_user_text(tool_context)
    event_words = ("meeting", "event", "appointment", "calendar invite", "call")
    reminder_words = ("remind", "reminder", "prepare", "task", "todo", "to-do")
    looks_like_event = any(word in title for word in event_words)
    looks_like_reminder = any(word in title for word in reminder_words)

    if looks_like_event and not looks_like_reminder:
        return {
            "error": (
                "This is a calendar event, not a task. Use "
                "create_calendar_event with the requested date/time."
            ),
            "original_request": user_text,
        }
    return None


def _after_tool_callback(tool, args, tool_context, tool_response):
    return make_json_safe(tool_response)


def _instruction(_context) -> str:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return f"""You are the Orchestrator — a senior AI planning agent.

Current local date/time: {now.isoformat()}.

Your job is to understand the user's request, break it into steps, call the
right tools, and then provide a concise final summary.

Tool areas:
- Tasks: create_task, get_tasks, update_task, delete_task
- Calendar: get_calendar_events, create_calendar_event
- Notes: save_note, get_notes, get_note, update_note, delete_note

**Multi-step requests**
For complex requests (e.g. "Schedule a meeting tomorrow at 5 and remind me to
prepare notes"), execute each step with the relevant tools in order.

**Scheduling and availability**
When the user asks to schedule something:
1. Parse the requested date/time into ISO-8601.
2. Use Asia/Kolkata (+05:30) when the user does not specify a timezone.
3. Use create_calendar_event for meetings, events, appointments, calls, haircuts,
   repairs, or anything that belongs on a calendar. Do not use create_task for
   those calendar items.
4. If they ask for an available/free time, first call get_calendar_events for
   that date, avoid overlapping events, then call create_calendar_event.
5. If the requested time is busy, pick the next open 1-hour slot between 09:00
   and 18:00 local time and explain the adjustment.
6. After create_calendar_event succeeds, always confirm the scheduled title,
   start time, and end time.

**Tasks and reminders**
Use create_task only for tasks, todos, and reminders. If the user says
"Schedule a meeting tomorrow at 3pm and remind me to prepare slides", call
create_calendar_event for the meeting and create_task only for "prepare slides".

**"Plan my day" workflow**
When the user asks you to plan their day:
1. Retrieve today's calendar events via get_calendar_events
2. Retrieve pending tasks via get_tasks
3. Retrieve recent notes via get_notes
4. Synthesise everything into a structured daily plan

**Rules**
- Do not call transfer_to_agent.
- Use tools for task, calendar, and note mutations; do not pretend an action is
  complete unless the relevant tool call succeeded.
- Provide a brief final summary after all steps complete.
- If a step fails, report the error and continue with remaining steps.
- Be concise and action-oriented in your summaries.
"""


orchestrator_agent = Agent(
    name="orchestrator",
    model="gemini-2.5-flash",
    description="Primary planning agent that coordinates tasks, calendar, and notes.",
    instruction=_instruction,
    tools=[
        create_task,
        get_tasks,
        update_task,
        delete_task,
        get_calendar_events,
        create_calendar_event,
        save_note,
        get_notes,
        get_note,
        update_note,
        delete_note,
    ],
    before_tool_callback=_before_tool_callback,
    after_tool_callback=_after_tool_callback,
)
