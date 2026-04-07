"""Task management tools — called by the Task Agent."""

from typing import Dict, List, Optional

from db.store import (
    create_task_doc,
    list_tasks_docs,
    update_task_doc,
    delete_task_doc,
)
from db.store import write_log
from utils.json_safety import make_json_safe

AGENT_NAME = "task_agent"


async def create_task(
    title: str,
    description: str = "",
    due_date: Optional[str] = None,
    priority: str = "medium",
) -> Dict:
    """Create a new task with the given details.

    Args:
        title: Short title for the task.
        description: Longer description (optional).
        due_date: ISO-8601 date string (optional).
        priority: One of low, medium, high.

    Returns:
        The created task document.
    """
    input_data = {
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
    }
    try:
        result = make_json_safe(
            await create_task_doc(title, description, due_date, priority)
        )
        await write_log(AGENT_NAME, "create_task", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "create_task", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def get_tasks(status: Optional[str] = None) -> List[Dict]:
    """Retrieve tasks, optionally filtered by status.

    Args:
        status: Filter by task status (pending, in_progress, done). None returns all.

    Returns:
        List of task documents.
    """
    input_data = {"status": status}
    try:
        result = make_json_safe(await list_tasks_docs(status_filter=status))
        await write_log(AGENT_NAME, "get_tasks", input_data, {"count": len(result)})
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "get_tasks", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict:
    """Update fields of an existing task.

    Args:
        task_id: The Firestore document ID of the task.
        title: New title for the task.
        description: New description for the task.
        due_date: New due date (ISO-8601 string).
        priority: New priority (low, medium, high).
        status: New status (pending, in_progress, done).

    Returns:
        The updated task document.
    """
    updates = {k: v for k, v in {
        "title": title, "description": description,
        "due_date": due_date, "priority": priority, "status": status,
    }.items() if v is not None}
    input_data = {"task_id": task_id, "updates": updates}
    try:
        result = make_json_safe(await update_task_doc(task_id, updates))
        if result is None:
            raise ValueError(f"Task {task_id} not found")
        await write_log(AGENT_NAME, "update_task", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "update_task", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def delete_task(task_id: str) -> Dict:
    """Delete a task by its ID.

    Args:
        task_id: The Firestore document ID of the task to delete.

    Returns:
        Confirmation message.
    """
    input_data = {"task_id": task_id}
    try:
        deleted = await delete_task_doc(task_id)
        if not deleted:
            raise ValueError(f"Task {task_id} not found")
        result = make_json_safe({"deleted": True, "task_id": task_id})
        await write_log(AGENT_NAME, "delete_task", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "delete_task", input_data, {},
            success=False, error_message=str(exc),
        )
        raise
