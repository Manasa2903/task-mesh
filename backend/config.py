"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent


def _resolve_backend_path(path: str) -> str:
    """Resolve relative backend config paths from either CWD or backend/."""
    if not path:
        return path

    configured_path = Path(path)
    if configured_path.is_absolute():
        return str(configured_path)

    cwd_path = configured_path.resolve()
    if cwd_path.exists():
        return str(cwd_path)

    backend_path = (BASE_DIR / configured_path).resolve()
    if backend_path.exists():
        return str(backend_path)

    return path


class Settings(BaseSettings):
    # Google Cloud
    google_cloud_project: str = ""
    google_application_credentials: str = ""

    # Gemini
    google_api_key: str = ""

    # Google Calendar OAuth
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    google_calendar_redirect_uri: str = "http://localhost:8000/auth/callback"
    google_calendar_id: str = "primary"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.google_application_credentials = _resolve_backend_path(
        settings.google_application_credentials
    )
    if settings.google_application_credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            settings.google_application_credentials
        )
    return settings
