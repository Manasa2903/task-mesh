"""Storage router — imports from Firestore repos if credentials are available,
otherwise falls back to the in-memory store for local development.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_USE_FIRESTORE = False

# Detect Firestore configuration. Do not make a network call at import time:
# it slows startup and can incorrectly force in-memory mode on transient DNS
# failures. CRUD calls will surface actual Firestore errors.
try:
    from config import get_settings
    settings = get_settings()

    # Check for emulator
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        _USE_FIRESTORE = True
    else:
        creds_path = settings.google_application_credentials
        if creds_path:
            if os.path.exists(creds_path):
                _USE_FIRESTORE = True
            else:
                logger.warning(
                    "Configured Firestore credentials file %s was not found; "
                    "using in-memory store.",
                    creds_path,
                )
                _USE_FIRESTORE = False
        else:
            # Try ADC only when no credentials path was explicitly configured.
            try:
                import google.auth
                google.auth.default()
                _USE_FIRESTORE = True
            except Exception:
                _USE_FIRESTORE = False
except Exception:
    _USE_FIRESTORE = False


if _USE_FIRESTORE:
    logger.info("Using Firestore for storage")
    from db.tasks_repo import create_task_doc, list_tasks_docs, update_task_doc, delete_task_doc
    from db.notes_repo import create_note_doc, list_notes_docs, get_note_doc, update_note_doc, delete_note_doc
    from db.logs_repo import write_log, list_logs
    from db.calendar_repo import create_calendar_event_doc, list_calendar_events_docs
    from db.chat_repo import add_chat_message, list_chat_messages, clear_chat_messages
else:
    logger.info("Firestore unavailable — using in-memory store")
    from db.memory_store import (
        create_task_doc,
        list_tasks_docs,
        update_task_doc,
        delete_task_doc,
        create_note_doc,
        list_notes_docs,
        get_note_doc,
        update_note_doc,
        delete_note_doc,
        write_log,
        list_logs,
        create_calendar_event_doc,
        list_calendar_events_docs,
        add_chat_message,
        list_chat_messages,
        clear_chat_messages,
    )
