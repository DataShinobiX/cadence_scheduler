# Quick Start Guide - Hackathon Edition

This guide will get you from zero to a working prototype in the fastest way possible.

---

## Prerequisites

### Required Software
- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Redis (or Docker)
- Git
- Node.js 18+ (for frontend, optional for MVP)

### Required Accounts
- OpenAI API account
- Google Cloud account (for Calendar & Gmail APIs)

---

## Phase 1: Environment Setup (30 minutes)

### Step 1: Create Project

```bash
# Create project directory
mkdir intelligent-scheduler
cd intelligent-scheduler

# Initialize git
git init

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create basic structure
mkdir -p app/{api/v1,agents,models,schemas,services,db,tasks,utils,core,orchestration}
mkdir -p docs tests scripts
touch app/__init__.py
```

### Step 2: Install Dependencies

Create `requirements.txt`:

```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Redis & Celery
redis==5.0.1
celery==5.3.6

# LangChain & AI
langchain==0.1.0
langchain-openai==0.0.2
langgraph==0.0.20
openai==1.10.0

# Google APIs
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.115.0

# Utilities
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0

# Vector Store (optional for MVP)
# chromadb==0.4.22

# Testing
pytest==7.4.4
httpx==0.26.0
```

Install:
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

Create `.env`:

```bash
# Application
APP_NAME=Intelligent Scheduler
DEBUG=true
SECRET_KEY=your-secret-key-change-this-in-production

# Database (use Docker)
DATABASE_URL=postgresql://scheduler:password@localhost:5432/scheduler_db

# Redis (use Docker)
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Google OAuth (set up later)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

### Step 4: Start Database & Redis (Docker)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: scheduler
      POSTGRES_PASSWORD: password
      POSTGRES_DB: scheduler_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Start services:
```bash
docker-compose up -d
```

Verify:
```bash
docker-compose ps  # Should show both running
```

---

## Phase 2: Core Setup (1 hour)

### Step 1: Configuration

Create `app/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Intelligent Scheduler"
    DEBUG: bool = False
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 2: Database Models

Create `app/db/base.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Create `app/models/user.py`:

```python
from sqlalchemy import Column, String, Boolean, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    timezone = Column(String(50), default="UTC")
    google_calendar_token = Column(String)
    gmail_token = Column(String)
    preferences = Column(JSON, default={})
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
```

Create `app/models/task.py`:

```python
from sqlalchemy import Column, String, Integer, Date, Time, TIMESTAMP, JSON, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    description = Column(String, nullable=False)
    original_input = Column(String)
    task_type = Column(String(50), default="user_requested")
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"))
    priority = Column(Integer, default=5)
    status = Column(String(50), default="pending")
    scheduled_date = Column(Date)
    start_time = Column(Time)
    duration_minutes = Column(Integer)
    deadline = Column(TIMESTAMP)
    location = Column(String(255))
    attendees = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    tags = Column(ARRAY(String))
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
```

### Step 3: Initialize Database

Create `scripts/init_db.py`:
 
```python
from app.db.base import Base, engine
from app.models.user import User
from app.models.task import Task
# Import other models...

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()
```

Run:
```bash
python scripts/init_db.py
```

---

## Phase 3: Build Agent 1 - Task Decomposer (2 hours)

### Create Agent Base Class

Create `app/agents/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic"""
        pass
```

### Create Task Decomposer

Create `app/agents/task_decomposer.py`:

```python
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.config import settings
from app.agents.base import BaseAgent

class TaskItem(BaseModel):
    description: str = Field(description="Task description")
    estimated_duration_minutes: int = Field(description="Estimated duration")
    location: str | None = Field(default=None)
    priority: int = Field(ge=1, le=10, default=5)
    time_constraint: str | None = Field(default=None)
    requires_coordination: bool = Field(default=False)
    contact_info: Dict[str, str] | None = Field(default=None)
    task_type: str = Field(default="user_requested")
    parent_task: str | None = Field(default=None)

class TaskList(BaseModel):
    tasks: List[TaskItem]

class TaskDecomposerAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert task decomposition assistant.

Break down user requests into atomic, schedulable tasks.

Rules:
1. If a task involves travel to a location, create THREE tasks:
   - Travel TO the location
   - The main activity
   - Travel BACK (if applicable)
2. Estimate realistic durations
3. Extract priority from language (urgent=1-3, normal=4-6, low=7-10)
4. Identify time constraints ("at 2PM", "after 5PM", "before EOD")
5. Extract contact info if mentioned

Output a list of tasks."""),
            ("user", "Break down this request:\n\n{transcript}")
        ])

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get structured output
            chain = self.prompt | self.llm.with_structured_output(TaskList)
            result = chain.invoke({"transcript": state["raw_transcript"]})

            # Update state
            state["decomposed_tasks"] = [task.model_dump() for task in result.tasks]
            return state

        except Exception as e:
            print(f"Error in TaskDecomposer: {e}")
            state["decomposed_tasks"] = []
            state["errors"] = state.get("errors", []) + [str(e)]
            return state
```

### Test Agent 1

Create `tests/test_task_decomposer.py`:

```python
from app.agents.task_decomposer import TaskDecomposerAgent

def test_task_decomposer():
    agent = TaskDecomposerAgent()

    state = {
        "user_id": "test-user",
        "raw_transcript": """
        I need to meet Bob at his office downtown at 2 PM to discuss the budget.
        Also, I must finish the pitch deck by end of day.
        And I want to go to the gym after 5 PM.
        """,
        "session_id": "test-session"
    }

    result = agent.execute(state)

    print("Decomposed tasks:")
    for i, task in enumerate(result["decomposed_tasks"], 1):
        print(f"{i}. {task['description']} ({task['estimated_duration_minutes']} min) - Priority: {task['priority']}")

if __name__ == "__main__":
    test_task_decomposer()
```

Run:
```bash
python -m pytest tests/test_task_decomposer.py -v -s
```

---

## Phase 4: Build API Endpoints (1 hour)

### Create FastAPI App

Create `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}

# Include routers
from app.api.v1 import schedule
app.include_router(schedule.router, prefix="/api/v1", tags=["schedule"])
```

### Create Schedule Endpoint

Create `app/schemas/schedule.py`:

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ScheduleRequest(BaseModel):
    user_id: str
    transcript: str

class ScheduleResponse(BaseModel):
    status: str
    session_id: str
    decomposed_tasks: List[Dict[str, Any]]
    scheduled_tasks: Optional[List[Dict[str, Any]]] = None
    conflicts: Optional[List[Dict[str, Any]]] = None
```

Create `app/api/v1/schedule.py`:

```python
from fastapi import APIRouter, HTTPException
from app.schemas.schedule import ScheduleRequest, ScheduleResponse
from app.agents.task_decomposer import TaskDecomposerAgent
import uuid

router = APIRouter()

@router.post("/schedule", response_model=ScheduleResponse)
async def schedule_tasks(request: ScheduleRequest):
    """
    Main scheduling endpoint
    """
    try:
        # Initialize state
        state = {
            "user_id": request.user_id,
            "raw_transcript": request.transcript,
            "session_id": str(uuid.uuid4()),
            "decomposed_tasks": [],
            "user_preferences": {},  # TODO: Fetch from DB
            "errors": []
        }

        # Agent 1: Decompose tasks
        decomposer = TaskDecomposerAgent()
        state = decomposer.execute(state)

        if state.get("errors"):
            raise HTTPException(status_code=500, detail=state["errors"])

        # For now, just return decomposed tasks
        # TODO: Add Agent 2 (Scheduler Brain) and Agent 3 (Calendar Integrator)

        return ScheduleResponse(
            status="success",
            session_id=state["session_id"],
            decomposed_tasks=state["decomposed_tasks"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Test API

Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

Test with curl:
```bash
curl -X POST "http://localhost:8000/api/v1/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "transcript": "I need to meet Bob downtown at 2 PM, finish the pitch deck by EOD, and go to the gym after 5 PM"
  }'
```

Or visit: http://localhost:8000/docs (interactive API docs)

---

## Phase 5: Google Calendar Integration (2 hours)

### Step 1: Set Up Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project: "Intelligent Scheduler"
3. Enable APIs:
   - Google Calendar API
   - Gmail API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/v1/auth/callback`
5. Download credentials JSON

### Step 2: Update .env

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

### Step 3: Create OAuth Flow

Create `app/api/v1/auth.py`:

```python
from fastapi import APIRouter, HTTPException, Depends
from google_auth_oauthlib.flow import Flow
from app.config import settings
from app.db.base import get_db
from sqlalchemy.orm import Session
from app.models.user import User
import json

router = APIRouter()

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly'
]

@router.get("/auth/google")
async def google_auth():
    """Initiate Google OAuth flow"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    return {"authorization_url": authorization_url}

@router.get("/auth/callback")
async def google_auth_callback(code: str, db: Session = Depends(get_db)):
    """Handle OAuth callback"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Get user info
    from googleapiclient.discovery import build
    service = build('calendar', 'v3', credentials=credentials)
    calendar = service.calendarList().get(calendarId='primary').execute()

    email = calendar.get('id')  # Primary calendar ID is the email

    # Save or update user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            google_calendar_token=credentials.to_json(),
            gmail_token=credentials.to_json()
        )
        db.add(user)
    else:
        user.google_calendar_token = credentials.to_json()
        user.gmail_token = credentials.to_json()

    db.commit()

    return {
        "status": "success",
        "user_id": str(user.user_id),
        "email": email,
        "message": "Google Calendar connected successfully"
    }
```

Add to `app/main.py`:
```python
from app.api.v1 import auth
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
```

### Step 4: Test OAuth Flow

1. Start server: `uvicorn app.main:app --reload`
2. Visit: http://localhost:8000/api/v1/auth/google
3. Click the authorization URL
4. Grant permissions
5. You'll be redirected back with your user_id

---

## Phase 6: Complete MVP (Remaining Time)

### Priority Order:

1. **Agent 2 (Scheduler Brain) - Basic Version** (3 hours)
   - Fetch calendar events
   - Simple time slot finding (no complex conflict resolution initially)
   - Return scheduled times

2. **Agent 3 (Calendar Integrator)** (1 hour)
   - Create events in Google Calendar
   - Update database

3. **Agent 4 (Email Tracker) - Basic** (2 hours)
   - Fetch recent emails
   - Extract deadlines with LLM
   - Create tasks

4. **Simple Frontend** (2 hours)
   - Voice input (Web Speech API)
   - Display schedule
   - Show conflicts

5. **Agent 5 (Recap Generator)** (1 hour)
   - Weekly summary generation
   - Basic metrics

---

## Deployment Checklist

### For Hackathon Demo:

1. **Environment Variables**
   ```bash
   # Copy .env to VM
   scp .env user@vm-ip:~/intelligent-scheduler/
   ```

2. **Docker Deployment**
   ```bash
   # On VM
   docker-compose up --build -d
   ```

3. **Database Migration**
   ```bash
   python scripts/init_db.py
   ```

4. **Test Endpoints**
   ```bash
   curl http://vm-ip:8000/health
   ```

---

## Debugging Tips

### Common Issues:

1. **LangGraph import errors**
   ```bash
   pip install --upgrade langchain langgraph
   ```

2. **Database connection errors**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps

   # View logs
   docker-compose logs db
   ```

3. **Google API errors**
   - Verify OAuth credentials
   - Check redirect URI matches exactly
   - Ensure APIs are enabled in Google Cloud Console

4. **OpenAI API errors**
   - Check API key is valid
   - Verify billing is set up
   - Check rate limits

---

## Time-Saving Tips for Hackathon

### Use Pre-built Tools:

1. **Swagger UI**: http://localhost:8000/docs - Test APIs without writing curl commands

2. **Database Viewer**: Use DBeaver or pgAdmin to inspect data

3. **Logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   ```

4. **Hot Reload**: Use `--reload` flag for uvicorn during development

5. **Skip ChromaDB for MVP**: Add it later if time permits

6. **Use Mock Data**: For testing, create sample users and tasks

---

## Sample Test Data

Create `scripts/seed_data.py`:

```python
from app.db.base import SessionLocal
from app.models.user import User
from app.models.task import Task
from datetime import datetime, timedelta
import uuid

def seed_data():
    db = SessionLocal()

    # Create test user
    user = User(
        email="test@example.com",
        name="Test User",
        timezone="America/New_York",
        preferences={
            "work_hours_start": "09:00",
            "work_hours_end": "17:00",
            "gym_preferred_time": "evening"
        }
    )
    db.add(user)
    db.commit()

    # Create sample tasks
    tasks = [
        Task(
            user_id=user.user_id,
            description="Finish project proposal",
            priority=1,
            deadline=datetime.now() + timedelta(hours=8),
            status="pending"
        ),
        Task(
            user_id=user.user_id,
            description="Team meeting",
            priority=3,
            scheduled_date=datetime.now().date(),
            start_time="14:00",
            duration_minutes=60,
            status="scheduled"
        )
    ]

    for task in tasks:
        db.add(task)

    db.commit()
    print(f"Seeded data for user: {user.email} (ID: {user.user_id})")

if __name__ == "__main__":
    seed_data()
```

---

## Next Steps

1. ✅ Set up environment
2. ✅ Build Agent 1
3. ✅ Create basic API
4. ⏳ Google Calendar integration
5. ⏳ Build Agent 2 & 3
6. ⏳ Add Agent 4 (Email)
7. ⏳ Build simple frontend
8. ⏳ Deploy to VM

Good luck with your hackathon! 🚀

## Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- LangChain Docs: https://python.langchain.com/
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- Google Calendar API: https://developers.google.com/calendar/api
- OpenAI API: https://platform.openai.com/docs/
