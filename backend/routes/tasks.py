"""Task routes — direct CRUD endpoints (bypass the AI layer)."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tools.task_tools import create_task, get_tasks, update_task, delete_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    due_date: Optional[str] = None
    priority: str = "medium"


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


@router.get("")
async def list_tasks(status: Optional[str] = None):
    """List tasks, optionally filtered by status."""
    try:
        return await get_tasks(status=status)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("", status_code=201)
async def add_task(req: CreateTaskRequest):
    """Create a new task."""
    try:
        return await create_task(
            title=req.title,
            description=req.description,
            due_date=req.due_date,
            priority=req.priority,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.patch("/{task_id}")
async def patch_task(task_id: str, req: UpdateTaskRequest):
    """Update a task by ID."""
    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return await update_task(task_id=task_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.delete("/{task_id}")
async def remove_task(task_id: str):
    """Delete a task by ID."""
    try:
        return await delete_task(task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
