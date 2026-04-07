"""TaskMesh — Multi-Agent AI System (FastAPI entry point)."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables BEFORE any other imports that depend on them
# Use the directory of this file to find .env, regardless of CWD
load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from routes.chat import router as chat_router
from routes.tasks import router as tasks_router
from routes.notes import router as notes_router
from routes.logs import router as logs_router
from routes.calendar import router as calendar_router

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("TaskMesh backend starting — env=%s", settings.app_env)
    yield
    logger.info("TaskMesh backend shutting down")


app = FastAPI(
    title="TaskMesh",
    description="Multi-agent AI system for tasks, schedules, and notes",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(tasks_router)
app.include_router(notes_router)
app.include_router(logs_router)
app.include_router(calendar_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "task-mesh"}


static_dir = Path(__file__).resolve().parent / "static"
assets_dir = static_dir / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "ok", "service": "task-mesh"}
