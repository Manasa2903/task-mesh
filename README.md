# TaskMesh — Multi-Agent AI System

A production-ready multi-agent AI system built entirely on Google Cloud technologies. TaskMesh helps users manage **tasks**, **schedules**, and **notes** by coordinating specialised AI agents through an orchestrator.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│          Chat  ·  Task Dashboard  ·  Execution Logs          │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                             │
│  POST /chat  ·  GET/POST /tasks  ·  GET /logs  ·  /notes    │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│               Orchestrator Agent (ADK)                       │
│          Intent parsing · Planning · Delegation              │
├──────────────┬──────────────┬────────────────────────────────┤
│  Task Agent  │ Calendar Agent│     Notes Agent               │
│  (ADK)       │  (ADK)       │      (ADK)                    │
├──────────────┼──────────────┼────────────────────────────────┤
│  Task Tools  │Calendar Tools│    Notes Tools                 │
│ create_task  │create_event  │   save_note                   │
│ get_tasks    │get_events    │   get_notes                   │
│ update_task  │              │   update_note                 │
│ delete_task  │              │   delete_note                 │
└──────┬───────┴──────┬───────┴─────────┬──────────────────────┘
       │              │                 │
┌──────▼──────────────▼─────────────────▼──────────────────────┐
│                    Firestore                                  │
│  tasks · notes · calendar_events · execution_logs            │
└──────────────────────────────────────────────────────────────┘
       │                          │
   Google Calendar API      Gemini 2.0 Flash
```

## Tech Stack

| Layer      | Technology                         |
| ---------- | ---------------------------------- |
| LLM        | Gemini 2.0 Flash (via Gemini API)  |
| Agents     | Google Agent Development Kit (ADK) |
| Backend    | Python 3.12 · FastAPI              |
| Database   | Cloud Firestore                    |
| Calendar   | Google Calendar API                |
| Frontend   | React 19 · Vite                    |
| Deployment | Cloud Run · Firebase Hosting       |

## Project Structure

```
task-mesh/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py    # Primary planning agent
│   │   ├── task_agent.py      # Task management sub-agent
│   │   ├── calendar_agent.py  # Calendar scheduling sub-agent
│   │   └── notes_agent.py     # Notes management sub-agent
│   ├── tools/
│   │   ├── task_tools.py      # create_task, get_tasks, etc.
│   │   ├── calendar_tools.py  # create_calendar_event, etc.
│   │   └── notes_tools.py     # save_note, get_notes, etc.
│   ├── db/
│   │   ├── __init__.py        # Firestore client singleton
│   │   ├── tasks_repo.py      # Tasks Firestore operations
│   │   ├── notes_repo.py      # Notes Firestore operations
│   │   └── logs_repo.py       # Execution logs storage
│   ├── services/
│   │   └── chat_service.py    # ADK Runner bridge
│   ├── routes/
│   │   ├── chat.py            # POST /chat
│   │   ├── tasks.py           # GET/POST/PATCH/DELETE /tasks
│   │   ├── notes.py           # GET/POST/PATCH/DELETE /notes
│   │   └── logs.py            # GET /logs
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # Pydantic settings
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx
│   │   │   ├── TasksPage.jsx
│   │   │   └── LogsPage.jsx
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── Dockerfile
├── cloudbuild.yaml
├── firebase.json
└── README.md
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Google Cloud SDK (`gcloud`)
- A GCP project with:
  - Firestore enabled (Native mode)
  - Gemini API enabled
  - Google Calendar API enabled (optional)

## Local Development

### 1. Clone and configure

```bash
cd task-mesh/backend
cp .env.example .env
# Edit .env with your GCP project ID and Gemini API key
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — the Vite dev server proxies API requests to the backend.

## Deployment to Google Cloud

### Option A: Manual deploy

```bash
# Set your project
export PROJECT_ID=your-gcp-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  calendar-json.googleapis.com \
  aiplatform.googleapis.com

# Create Firestore database (if not exists)
gcloud firestore databases create --location=us-central1

# Build and push container
gcloud builds submit --tag gcr.io/$PROJECT_ID/task-mesh

# Deploy to Cloud Run
gcloud run deploy task-mesh \
  --image gcr.io/$PROJECT_ID/task-mesh \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_API_KEY=your-key" \
  --memory 512Mi \
  --cpu 1
```

### Option B: Cloud Build (CI/CD)

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Deploy frontend to Firebase Hosting

```bash
cd frontend && npm run build
firebase deploy --only hosting
```

## Sample Test Queries

Use these with the chat interface to demo the multi-agent system:

| Query                                                                                     | Expected Behavior                                                           |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `Create a task to review the Q4 report by Friday`                                         | Orchestrator → Task Agent → `create_task()`                                 |
| `Show me my tasks`                                                                        | Orchestrator → Task Agent → `get_tasks()`                                   |
| `Schedule a meeting tomorrow at 3pm`                                                      | Orchestrator → Calendar Agent → `create_calendar_event()`                   |
| `Save a note about the project requirements`                                              | Orchestrator → Notes Agent → `save_note()`                                  |
| `Schedule a meeting tomorrow at 5 and remind me to prepare notes`                         | Orchestrator → Calendar Agent + Notes Agent (multi-step)                    |
| `Plan my day`                                                                             | Orchestrator → Calendar Agent + Task Agent + Notes Agent → synthesised plan |
| `Create a high-priority task to fix the login bug and save a note with the error details` | Multi-agent, multi-tool workflow                                            |

## Multi-Step Workflow Example

**User:** "Schedule a meeting tomorrow at 5 and remind me to prepare notes"

**Execution trace:**

1. Orchestrator parses intent → identifies 2 actions needed
2. Delegates to **Calendar Agent** → calls `create_calendar_event()`
3. Delegates to **Notes Agent** → calls `save_note()` with reminder content
4. Orchestrator summarises both results

All steps are logged to Firestore `execution_logs` collection with:

- Agent name
- Tool called
- Input/output
- Timestamp
- Success/failure status

## Key Design Decisions

- **Tools, not direct access**: Agents call tool functions — they never access Firestore or APIs directly. This ensures every action is logged and testable.
- **Firestore execution logs**: Every tool invocation is recorded, providing a complete audit trail visible in the Logs panel.
- **Calendar API fallback**: When Google Calendar credentials aren't configured, events are stored in Firestore. This lets the system work in development without OAuth setup.
- **ADK session management**: The chat service uses ADK's `InMemorySessionService` for context continuity within a conversation. For production, swap to a persistent session store.
- **Async throughout**: All DB operations and agent interactions use `async/await` for non-blocking execution.

## Architecture Notes (AlloyDB)

For production workloads requiring complex queries, analytics, or relational data:

- **AlloyDB** can replace or supplement Firestore for structured task/note data
- Use AlloyDB for cross-entity queries, reporting dashboards, and data that benefits from SQL
- Keep Firestore for execution logs (high write throughput, schema-flexible) and real-time subscriptions
- AlloyDB is PostgreSQL-compatible, so standard ORMs (SQLAlchemy, asyncpg) work out of the box
