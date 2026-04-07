"""Firestore database client singleton."""

from __future__ import annotations

import logging
import os
from typing import Optional

from google.cloud import firestore
from config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[firestore.AsyncClient] = None


def get_firestore_client() -> firestore.AsyncClient:
    """Return a cached async Firestore client.

    Uses Application Default Credentials (ADC) when no explicit service
    account file is found.  Run ``gcloud auth application-default login``
    for local development.
    """
    global _client
    if _client is None:
        settings = get_settings()

        # If the configured credentials file doesn't exist, fall back to ADC
        creds_path = settings.google_application_credentials
        if creds_path and not os.path.isabs(creds_path):
            creds_path = os.path.join(os.path.dirname(__file__), "..", creds_path)
        if creds_path and not os.path.exists(creds_path):
            logger.warning(
                "Service account file %s not found — using Application Default Credentials. "
                "Run 'gcloud auth application-default login' for local dev.",
                settings.google_application_credentials,
            )
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

        project = settings.google_cloud_project or None
        _client = firestore.AsyncClient(project=project)
    return _client


# Collection names
TASKS_COLLECTION = "tasks"
NOTES_COLLECTION = "notes"
LOGS_COLLECTION = "execution_logs"
CALENDAR_EVENTS_COLLECTION = "calendar_events"
CHAT_MESSAGES_COLLECTION = "chat_messages"
