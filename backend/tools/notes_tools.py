"""Notes tools — called by the Notes Agent."""

from typing import Dict, List, Optional

from db.store import (
    create_note_doc,
    list_notes_docs,
    get_note_doc,
    update_note_doc,
    delete_note_doc,
)
from db.store import write_log
from utils.json_safety import make_json_safe

AGENT_NAME = "notes_agent"


async def save_note(
    title: str,
    content: str,
    tags: Optional[str] = None,
) -> Dict:
    """Save a new note.

    Args:
        title: Note title.
        content: The body / content of the note.
        tags: Optional comma-separated tags for categorisation.

    Returns:
        The created note document.
    """
    tags_list = [t.strip() for t in tags.split(",")] if tags else []
    input_data = {"title": title, "content": content, "tags": tags_list}
    try:
        result = make_json_safe(await create_note_doc(title, content, tags_list))
        await write_log(AGENT_NAME, "save_note", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "save_note", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def get_notes() -> List[Dict]:
    """Retrieve all notes.

    Returns:
        List of note documents.
    """
    input_data = {}
    try:
        result = make_json_safe(await list_notes_docs())
        await write_log(AGENT_NAME, "get_notes", input_data, {"count": len(result)})
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "get_notes", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def get_note(note_id: str) -> Dict:
    """Retrieve a single note by ID.

    Args:
        note_id: The Firestore document ID.

    Returns:
        The note document.
    """
    input_data = {"note_id": note_id}
    try:
        result = make_json_safe(await get_note_doc(note_id))
        if result is None:
            raise ValueError(f"Note {note_id} not found")
        await write_log(AGENT_NAME, "get_note", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "get_note", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def update_note(
    note_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[str] = None,
) -> Dict:
    """Update an existing note.

    Args:
        note_id: The Firestore document ID.
        title: New title for the note.
        content: New body content for the note.
        tags: New comma-separated tags for the note.

    Returns:
        The updated note document.
    """
    parsed_tags = [t.strip() for t in tags.split(",")] if tags else None
    updates = {k: v for k, v in {
        "title": title, "content": content, "tags": parsed_tags,
    }.items() if v is not None}
    input_data = {"note_id": note_id, "updates": updates}
    try:
        result = make_json_safe(await update_note_doc(note_id, updates))
        if result is None:
            raise ValueError(f"Note {note_id} not found")
        await write_log(AGENT_NAME, "update_note", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "update_note", input_data, {},
            success=False, error_message=str(exc),
        )
        raise


async def delete_note(note_id: str) -> Dict:
    """Delete a note by ID.

    Args:
        note_id: The Firestore document ID.

    Returns:
        Confirmation message.
    """
    input_data = {"note_id": note_id}
    try:
        deleted = await delete_note_doc(note_id)
        if not deleted:
            raise ValueError(f"Note {note_id} not found")
        result = make_json_safe({"deleted": True, "note_id": note_id})
        await write_log(AGENT_NAME, "delete_note", input_data, result)
        return result
    except Exception as exc:
        await write_log(
            AGENT_NAME, "delete_note", input_data, {},
            success=False, error_message=str(exc),
        )
        raise
