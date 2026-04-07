"""Notes Agent — saves and retrieves notes via tool functions.

Uses Google ADK's Agent class with Gemini as the underlying LLM.
"""

from google.adk.agents import Agent
from tools.notes_tools import save_note, get_notes, get_note, update_note, delete_note

notes_agent = Agent(
    name="notes_agent",
    model="gemini-2.5-flash",
    description="Creates, retrieves, updates, and deletes user notes.",
    instruction="""You are the Notes Agent. You manage all note-taking operations.

When the user wants to:
- Save a note → call save_note with title, content, and optional tags
- List notes → call get_notes
- View a specific note → call get_note with the note_id
- Update a note → call update_note with note_id and updated fields
- Delete a note → call delete_note with the note_id

Infer a suitable title from the content if the user doesn't supply one.
Always confirm what you stored.
""",
    tools=[save_note, get_notes, get_note, update_note, delete_note],
)
