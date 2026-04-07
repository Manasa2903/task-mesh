"""Notes routes — direct CRUD endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tools.notes_tools import save_note, get_notes, get_note, update_note, delete_note

router = APIRouter(prefix="/notes", tags=["notes"])


class CreateNoteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None


class UpdateNoteRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("")
async def list_notes():
    """List all notes."""
    try:
        return await get_notes()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/{note_id}")
async def read_note(note_id: str):
    """Get a single note by ID."""
    try:
        return await get_note(note_id=note_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("", status_code=201)
async def add_note(req: CreateNoteRequest):
    """Create a new note."""
    tags = ",".join(req.tags) if req.tags else None
    try:
        return await save_note(title=req.title, content=req.content, tags=tags)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.patch("/{note_id}")
async def patch_note(note_id: str, req: UpdateNoteRequest):
    """Update a note by ID."""
    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "tags" in updates:
        updates["tags"] = ",".join(updates["tags"]) if updates["tags"] else None
    try:
        return await update_note(note_id=note_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.delete("/{note_id}")
async def remove_note(note_id: str):
    """Delete a note by ID."""
    try:
        return await delete_note(note_id=note_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
