"""Task Agent — manages tasks via tool functions.

Uses Google ADK's Agent class with Gemini as the underlying LLM.
"""

from google.adk.agents import Agent
from tools.task_tools import create_task, get_tasks, update_task, delete_task

task_agent = Agent(
    name="task_agent",
    model="gemini-2.5-flash",
    description="Manages user tasks — creating, listing, updating, and deleting tasks.",
    instruction="""You are the Task Agent. Your sole responsibility is managing tasks.

When the user wants to:
- Create a task → call create_task with title, description, due_date, priority
- List tasks → call get_tasks, optionally with a status filter
- Update a task → call update_task with the task_id and the fields to change
- Delete a task → call delete_task with the task_id

Always confirm the action you took and provide relevant details back to the user.
If information is missing (e.g. no title for a new task), ask the user.
Use "medium" as default priority if not specified.
""",
    tools=[create_task, get_tasks, update_task, delete_task],
)
