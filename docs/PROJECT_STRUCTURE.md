# Project Structure

## Recommended Directory Structure

```
intelligent-scheduler/
├── .env.example                 # Environment variables template
├── .gitignore
├── docker-compose.yml           # Container orchestration
├── Dockerfile
├── README.md
├── requirements.txt             # Python dependencies
├── alembic.ini                  # Database migration config
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration management
│   ├── dependencies.py          # FastAPI dependencies
│   │
│   ├── api/                     # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── schedule.py      # POST /schedule, /resolve-conflict
│   │   │   ├── tasks.py         # GET/PUT/DELETE /tasks
│   │   │   ├── calendar.py      # GET /calendar, /sync
│   │   │   ├── recap.py         # GET /recap
│   │   │   └── auth.py          # OAuth endpoints
│   │
│   ├── agents/                  # AI Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent class
│   │   ├── task_decomposer.py   # Agent 1
│   │   ├── scheduler_brain.py   # Agent 2
│   │   ├── calendar_integrator.py # Agent 3
│   │   ├── email_tracker.py     # Agent 4
│   │   ├── recap_generator.py   # Agent 5
│   │   └── prompts/             # LLM prompts
│   │       ├── decomposer.txt
│   │       ├── scheduler.txt
│   │       └── recap.txt
│   │
│   ├── orchestration/           # LangGraph workflows
│   │   ├── __init__.py
│   │   ├── state.py             # AgentState definition
│   │   ├── scheduler_graph.py   # Main scheduling workflow
│   │   └── nodes.py             # Graph node functions
│   │
│   ├── models/                  # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── calendar_event.py
│   │   ├── email_tracking.py
│   │   ├── agent_context.py
│   │   ├── weekly_recap.py
│   │   └── conflict.py
│   │
│   ├── schemas/                 # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── schedule.py
│   │   ├── task.py
│   │   ├── calendar.py
│   │   └── user.py
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── google_calendar.py   # Google Calendar API wrapper
│   │   ├── gmail.py             # Gmail API wrapper
│   │   ├── llm.py               # OpenAI API wrapper
│   │   ├── conflict_resolver.py # Conflict detection & resolution
│   │   ├── vector_store.py      # ChromaDB operations
│   │   └── cache.py             # Redis caching
│   │
│   ├── db/                      # Database utilities
│   │   ├── __init__.py
│   │   ├── session.py           # Database session management
│   │   ├── base.py              # SQLAlchemy base
│   │   └── init_db.py           # Database initialization
│   │
│   ├── tasks/                   # Celery background tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery configuration
│   │   ├── email_sync.py        # Email tracking task
│   │   ├── calendar_sync.py     # Calendar sync task
│   │   └── recap_generation.py  # Weekly recap task
│   │
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── auth.py              # OAuth helpers
│   │   ├── time.py              # Time/timezone utilities
│   │   ├── crypto.py            # Encryption/decryption
│   │   └── validators.py        # Input validation
│   │
│   └── core/                    # Core functionality
│       ├── __init__.py
│       ├── exceptions.py        # Custom exceptions
│       ├── logging.py           # Logging configuration
│       └── middleware.py        # FastAPI middleware
│
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
│
├── frontend/                    # Web UI (optional for MVP)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_agents/
│   │   ├── test_decomposer.py
│   │   ├── test_scheduler_brain.py
│   │   └── test_calendar_integrator.py
│   ├── test_api/
│   │   ├── test_schedule.py
│   │   └── test_tasks.py
│   └── test_services/
│       ├── test_google_calendar.py
│       └── test_conflict_resolver.py
│
├── scripts/                     # Utility scripts
│   ├── setup_db.py              # Database setup
│   ├── seed_data.py             # Sample data for testing
│   └── deploy.sh                # Deployment script
│
└── docs/                        # Documentation
    ├── SOLUTION_ARCHITECTURE.md
    ├── database_schema.sql
    ├── API.md                   # API documentation
    └── DEPLOYMENT.md            # Deployment guide
```

---

## Key Files Explained

### `app/main.py`
FastAPI application entry point. Initializes the app, includes routers, sets up middleware.

```python
from fastapi import FastAPI
from app.api.v1 import schedule, tasks, calendar, recap, auth
from app.core.middleware import setup_middleware
from app.core.logging import setup_logging

app = FastAPI(title="Intelligent Scheduler", version="1.0.0")

setup_middleware(app)
setup_logging()

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(schedule.router, prefix="/api/v1", tags=["schedule"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(recap.router, prefix="/api/v1/recap", tags=["recap"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### `app/config.py`
Centralized configuration using Pydantic Settings.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Intelligent Scheduler"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5

    # Redis
    REDIS_URL: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### `app/orchestration/state.py`
LangGraph state definition.

```python
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime

class AgentState(TypedDict):
    # User context
    user_id: str
    session_id: str
    raw_transcript: str

    # Agent 1: Task Decomposer output
    decomposed_tasks: List[Dict[str, Any]]

    # Agent 2: Scheduler Brain output
    scheduling_plan: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    needs_user_input: bool
    user_feedback: Optional[str]

    # Agent 3: Calendar Integrator output
    scheduled_events: List[str]

    # Shared context
    existing_calendar: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    conversation_history: List[str]

    # Error handling
    errors: List[str]
```

### `app/orchestration/scheduler_graph.py`
Main LangGraph workflow.

```python
from langgraph.graph import StateGraph, END
from app.orchestration.state import AgentState
from app.agents.task_decomposer import TaskDecomposerAgent
from app.agents.scheduler_brain import SchedulerBrainAgent
from app.agents.calendar_integrator import CalendarIntegratorAgent

def create_scheduler_graph():
    workflow = StateGraph(AgentState)

    # Initialize agents
    decomposer = TaskDecomposerAgent()
    scheduler = SchedulerBrainAgent()
    integrator = CalendarIntegratorAgent()

    # Add nodes
    workflow.add_node("decompose", decomposer.execute)
    workflow.add_node("schedule", scheduler.execute)
    workflow.add_node("integrate", integrator.execute)
    workflow.add_node("ask_user", ask_user_node)

    # Add edges
    workflow.add_edge("decompose", "schedule")

    # Conditional routing based on conflicts
    workflow.add_conditional_edges(
        "schedule",
        route_after_scheduling,
        {
            "ask_user": "ask_user",
            "integrate": "integrate"
        }
    )

    workflow.add_edge("ask_user", "schedule")  # Loop back
    workflow.add_edge("integrate", END)

    workflow.set_entry_point("decompose")

    return workflow.compile()

def route_after_scheduling(state: AgentState) -> str:
    return "ask_user" if state["needs_user_input"] else "integrate"

def ask_user_node(state: AgentState) -> AgentState:
    # This is a placeholder - actual implementation would
    # pause execution and wait for user input via API
    return state
```

### `app/tasks/celery_app.py`
Celery configuration for background tasks.

```python
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "scheduler",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    'sync-emails-every-30-min': {
        'task': 'app.tasks.email_sync.sync_all_users_emails',
        'schedule': crontab(minute='*/30'),
    },
    'sync-calendars-every-hour': {
        'task': 'app.tasks.calendar_sync.sync_all_users_calendars',
        'schedule': crontab(minute=0),
    },
    'generate-weekly-recaps': {
        'task': 'app.tasks.recap_generation.generate_all_recaps',
        'schedule': crontab(hour=20, minute=0, day_of_week=0),  # Sunday 8 PM
    },
}

celery_app.autodiscover_tasks(['app.tasks'])
```

---

## Dependencies (`requirements.txt`)

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Redis & Caching
redis==5.0.1
celery==5.3.6

# LangChain & AI
langchain==0.1.0
langchain-openai==0.0.2
langgraph==0.0.20
openai==1.10.0

# Vector Store
chromadb==0.4.22

# Google APIs
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.115.0

# Utilities
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.26.0

# Logging & Monitoring
structlog==24.1.0
sentry-sdk==1.40.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0

# Development
black==24.1.1
ruff==0.1.14
mypy==1.8.0
```

---

## Environment Variables (`.env.example`)

```bash
# Application
APP_NAME=Intelligent Scheduler
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/scheduler_db

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_data
```

---

## Docker Compose Configuration

See the main SOLUTION_ARCHITECTURE.md for the complete `docker-compose.yml` file.

---

## Database Migrations with Alembic

### Initial Setup
```bash
# Initialize Alembic (already done if following structure)
alembic init alembic

# Create first migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### During Development
```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add new field to tasks"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Running the Application

### Development (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
python scripts/setup_db.py

# Run migrations
alembic upgrade head

# Start Redis
redis-server

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info

# Start FastAPI
uvicorn app.main:app --reload --port 8000
```

### Production (with Docker)
```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_agents/test_scheduler_brain.py -v
```

---

## Git Ignore Recommendations

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Environment
.env
.env.local

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# ChromaDB
chroma_data/

# Coverage
htmlcov/
.coverage
.pytest_cache/

# Docker
docker-compose.override.yml
```

---

## Next Steps

1. **Clone/Initialize Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial project structure"
   ```

2. **Set Up Development Environment**
   - Create virtual environment: `python -m venv venv`
   - Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
   - Install dependencies: `pip install -r requirements.txt`

3. **Set Up External Services**
   - Create Google Cloud project
   - Enable Calendar & Gmail APIs
   - Create OAuth credentials
   - Get OpenAI API key

4. **Initialize Database**
   - Start PostgreSQL (via Docker or locally)
   - Run migrations: `alembic upgrade head`

5. **Start Development**
   - Follow the implementation roadmap in SOLUTION_ARCHITECTURE.md
   - Start with Agent 1 (Task Decomposer)
   - Build incrementally, test frequently

---

## Useful Commands Cheatsheet

```bash
# Database
alembic upgrade head              # Apply migrations
alembic revision --autogenerate   # Create migration
psql -U user -d scheduler_db      # Connect to database

# Celery
celery -A app.tasks.celery_app worker --loglevel=info  # Start worker
celery -A app.tasks.celery_app beat --loglevel=info    # Start beat
celery -A app.tasks.celery_app flower                  # Monitoring UI

# FastAPI
uvicorn app.main:app --reload --port 8000  # Development
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Production

# Docker
docker-compose up --build         # Build and start
docker-compose down -v            # Stop and remove volumes
docker-compose logs -f web        # View logs for specific service
docker-compose exec web bash      # Access container shell

# Testing
pytest -v                         # Verbose output
pytest -k "test_scheduler"        # Run specific tests
pytest --pdb                      # Debug on failure
```
