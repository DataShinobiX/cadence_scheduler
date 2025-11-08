# Intelligent Scheduler - Solution Architecture

## Executive Summary

An agentic AI-powered scheduling assistant that processes natural language input, intelligently schedules tasks, manages conflicts, tracks commitments, and provides weekly recaps.

---

## 1. Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **LLM**: OpenAI GPT-4 (with function calling for structured outputs)
- **Agent Framework**: **LangGraph** (preferred for complex multi-agent orchestration with state management)
  - Alternative: CrewAI (simpler but less control)
- **Backend Framework**: **FastAPI** (async, modern, fast)
- **Database**: **PostgreSQL** (robust, supports JSON columns for flexibility)
  - Development: SQLite for quick prototyping
- **Cache/Queue**: **Redis** (for task queues and session management)
- **Vector Store**: **ChromaDB** (embedded, for user history/context retrieval)

### Integrations
- **Calendar**: **Google Calendar API** (most widely used, robust documentation)
- **Email**: **Gmail API** (integrates well with Google Calendar)
- **Speech-to-Text**: OpenAI Whisper API or Web Speech API

### Frontend (Lightweight for MVP)
- **Framework**: React with Vite or simple HTML/JS
- **UI Components**: Tailwind CSS
- **Real-time Updates**: Server-Sent Events (SSE) or WebSockets

### Deployment
- **Containerization**: Docker + Docker Compose
- **Web Server**: Uvicorn (ASGI server)
- **Reverse Proxy**: Nginx (if needed)
- **VM Hosting**: Ubuntu 22.04 LTS

---

## 2. System Architecture

### Architecture Pattern: **Modular Monolith with Agent Orchestration**

For a hackathon, a modular monolith is optimal (faster development, easier debugging) with clear separation between agents.

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                  (Web App / Voice Input)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LANGGRAPH ORCHESTRATOR                      │  │
│  │            (Manages Agent State & Flow)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent 4  │       │
│  │  Task    │─▶│Scheduler │─▶│Calendar  │  │  Email   │       │
│  │Decomposer│  │  Brain   │  │Integrator│  │ Tracker  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                      │                                          │
│                      ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AGENT 5: RECAP GENERATOR                    │  │
│  │              (Runs weekly as background job)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │    Redis     │  │  ChromaDB    │          │
│  │ (Main DB)    │  │ (Queue/Cache)│  │  (Vectors)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Google Calendar│  │  Gmail API  │  │  OpenAI API  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

### PostgreSQL Tables

#### users
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    google_calendar_token TEXT,
    gmail_token TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### tasks
```sql
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    original_input TEXT, -- Original speech transcript
    task_type VARCHAR(50), -- 'user_requested', 'email_derived', 'decomposed'
    parent_task_id UUID REFERENCES tasks(task_id), -- For decomposed tasks
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    status VARCHAR(50) DEFAULT 'pending', -- pending, scheduled, completed, cancelled
    scheduled_date DATE,
    start_time TIME,
    duration_minutes INTEGER,
    location VARCHAR(255),
    metadata JSONB DEFAULT '{}', -- Flexible field for agent-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### calendar_events
```sql
CREATE TABLE calendar_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    google_event_id VARCHAR(255) UNIQUE,
    task_id UUID REFERENCES tasks(task_id), -- NULL if external event
    summary TEXT,
    description TEXT,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    location VARCHAR(255),
    attendees JSONB DEFAULT '[]',
    is_external BOOLEAN DEFAULT false, -- True if not created by our system
    is_movable BOOLEAN DEFAULT true, -- Can this event be rescheduled?
    sync_status VARCHAR(50) DEFAULT 'synced',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### email_tracking
```sql
CREATE TABLE email_tracking (
    email_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    gmail_message_id VARCHAR(255) UNIQUE,
    subject TEXT,
    sender VARCHAR(255),
    received_at TIMESTAMP,
    extracted_deadline TIMESTAMP,
    extracted_task_description TEXT,
    processed BOOLEAN DEFAULT false,
    task_id UUID REFERENCES tasks(task_id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### agent_context
```sql
CREATE TABLE agent_context (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- Groups related agent runs
    agent_name VARCHAR(100),
    context_type VARCHAR(50), -- 'input', 'output', 'state'
    context_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### weekly_recaps
```sql
CREATE TABLE weekly_recaps (
    recap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    total_tasks_planned INTEGER,
    total_tasks_completed INTEGER,
    productivity_score DECIMAL(3,2), -- 0.00 to 1.00
    work_life_balance_score DECIMAL(3,2),
    summary TEXT,
    recommendations TEXT,
    highlights JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes
```sql
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_scheduled_date ON tasks(scheduled_date) WHERE status = 'scheduled';
CREATE INDEX idx_calendar_events_user_time ON calendar_events(user_id, start_datetime);
CREATE INDEX idx_email_tracking_processed ON email_tracking(user_id, processed);
```

---

## 4. Agent Design & Architecture

### Agent Framework: LangGraph

**Why LangGraph?**
- Built-in state management (critical for multi-agent context sharing)
- Supports conditional edges (for conflict resolution)
- Persistent checkpointing
- Easy to visualize agent flow
- Better control than CrewAI for complex workflows

### Agent State Schema

```python
from typing import TypedDict, List, Optional
from datetime import datetime

class AgentState(TypedDict):
    # User input
    user_id: str
    raw_transcript: str
    session_id: str

    # Agent 1 output
    decomposed_tasks: List[dict]  # [{description, estimated_duration, location, priority}]

    # Agent 2 output
    scheduling_plan: List[dict]  # [{task_id, date, start_time, duration, location, conflicts}]
    conflicts: List[dict]  # [{conflict_type, details, suggestions}]
    needs_user_input: bool
    user_feedback: Optional[str]

    # Agent 3 output
    scheduled_events: List[str]  # Calendar event IDs

    # Shared context
    existing_calendar: List[dict]  # Current calendar state
    user_preferences: dict
    conversation_history: List[str]
```

### Agent Implementations

#### Agent 1: Task Decomposer

**Responsibilities:**
- Parse natural language transcript
- Identify individual tasks
- Decompose complex tasks (e.g., "meeting across town" → travel + meeting + return)
- Extract: task description, priority, time constraints, location

**Implementation:**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class TaskDecomposerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert task decomposer.
            Break down user requests into atomic, schedulable tasks.

            Rules:
            1. If a task involves travel, create separate tasks for:
               - Travel to location
               - The main activity
               - Travel back (if applicable)
            2. Estimate realistic durations
            3. Identify task dependencies
            4. Extract priority signals (urgent, must, important, etc.)
            5. Identify time constraints (before 5PM, this week, etc.)

            Output JSON array of tasks with:
            - description
            - estimated_duration_minutes
            - location (if applicable)
            - priority (1-10, 1 = highest)
            - time_constraint (string or null)
            - requires_coordination (bool, if involves others)
            - contact_info (if mentioned)
            """),
            ("user", "{transcript}")
        ])

    def decompose(self, state: AgentState) -> AgentState:
        # Use function calling for structured output
        response = self.llm.with_structured_output(TaskList).invoke(
            self.prompt.format(transcript=state["raw_transcript"])
        )
        state["decomposed_tasks"] = response.tasks
        return state
```

#### Agent 2: Scheduler Brain (Most Complex)

**Responsibilities:**
- Fetch current calendar state
- Prioritize tasks using context (user preferences, deadlines, energy levels)
- Find optimal time slots
- Detect conflicts
- Generate alternatives if conflicts exist
- Decide what needs user confirmation

**Implementation Strategy:**
```python
class SchedulerBrainAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)

    def schedule(self, state: AgentState) -> AgentState:
        # 1. Fetch existing calendar
        existing_events = self._get_calendar_events(state["user_id"])
        state["existing_calendar"] = existing_events

        # 2. Build time availability matrix
        availability = self._build_availability_matrix(existing_events)

        # 3. Use LLM to intelligently schedule
        scheduling_prompt = self._build_scheduling_prompt(
            tasks=state["decomposed_tasks"],
            availability=availability,
            user_prefs=state["user_preferences"]
        )

        # Use function calling for structured output
        result = self.llm.with_structured_output(SchedulingPlan).invoke(
            scheduling_prompt
        )

        # 4. Detect conflicts
        conflicts = self._detect_conflicts(result.planned_tasks, existing_events)

        if conflicts:
            state["conflicts"] = conflicts
            state["needs_user_input"] = self._requires_user_decision(conflicts)
            # Generate alternatives
            alternatives = self._generate_alternatives(conflicts, availability)
            state["scheduling_plan"] = alternatives
        else:
            state["scheduling_plan"] = result.planned_tasks
            state["needs_user_input"] = False

        return state

    def _build_availability_matrix(self, events):
        # Create 15-minute slot matrix for next 7 days
        # Mark occupied slots
        pass

    def _detect_conflicts(self, planned_tasks, existing_events):
        # Check for overlaps
        # Identify immovable events
        pass
```

#### Agent 3: Calendar Integrator

**Responsibilities:**
- Take finalized schedule from Agent 2
- Create events in Google Calendar
- Handle API errors gracefully
- Update database with event IDs

**Implementation:**
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class CalendarIntegratorAgent:
    def __init__(self):
        self.service = None

    def integrate(self, state: AgentState) -> AgentState:
        user = self._get_user(state["user_id"])
        self.service = self._build_calendar_service(user.google_calendar_token)

        scheduled_event_ids = []
        for task in state["scheduling_plan"]:
            event = {
                'summary': task['description'],
                'location': task.get('location', ''),
                'start': {
                    'dateTime': f"{task['date']}T{task['start_time']}",
                    'timeZone': user.timezone,
                },
                'end': {
                    'dateTime': self._calculate_end_time(task),
                    'timeZone': user.timezone,
                },
            }

            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            scheduled_event_ids.append(created_event['id'])

            # Update database
            self._save_to_db(task, created_event['id'], user.user_id)

        state["scheduled_events"] = scheduled_event_ids
        return state
```

#### Agent 4: Email Tracker

**Responsibilities:**
- Periodically check Gmail for new emails
- Extract deadlines, meeting requests, assignments
- Create tasks automatically
- Run as background job (Celery task)

**Implementation:**
```python
from celery import Celery
import re
from datetime import datetime

celery_app = Celery('tasks', broker='redis://localhost:6379')

@celery_app.task
def track_emails_for_user(user_id: str):
    agent = EmailTrackerAgent()
    agent.process_user_emails(user_id)

class EmailTrackerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)

    def process_user_emails(self, user_id: str):
        gmail_service = self._build_gmail_service(user_id)

        # Fetch unread emails from last 24 hours
        messages = gmail_service.users().messages().list(
            userId='me',
            q='is:unread newer_than:1d'
        ).execute()

        for msg in messages.get('messages', []):
            email_data = self._get_email_content(gmail_service, msg['id'])

            # Use LLM to extract actionable items
            extraction_prompt = f"""
            Analyze this email and extract any deadlines, tasks, or commitments.

            Subject: {email_data['subject']}
            From: {email_data['from']}
            Body: {email_data['body']}

            Extract:
            - Any explicit deadlines (dates/times)
            - Tasks or assignments mentioned
            - Meeting requests
            - Priority level

            Output JSON.
            """

            extracted = self.llm.with_structured_output(EmailExtraction).invoke(
                extraction_prompt
            )

            if extracted.has_actionable_items:
                # Create tasks
                self._create_tasks_from_email(
                    user_id,
                    extracted,
                    email_data
                )
```

#### Agent 5: Recap Generator

**Responsibilities:**
- Run weekly (Sunday night or Monday morning)
- Analyze completed vs. planned tasks
- Calculate productivity metrics
- Identify patterns (e.g., always skips gym)
- Generate motivational insights

**Implementation:**
```python
class RecapGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    def generate_weekly_recap(self, user_id: str, week_start: datetime):
        # Fetch data
        tasks = self._get_tasks_for_week(user_id, week_start)
        calendar_events = self._get_calendar_events_for_week(user_id, week_start)

        # Calculate metrics
        total_planned = len([t for t in tasks if t.status in ['scheduled', 'completed']])
        total_completed = len([t for t in tasks if t.status == 'completed'])
        completion_rate = total_completed / total_planned if total_planned > 0 else 0

        # Categorize tasks
        work_tasks = [t for t in tasks if self._is_work_task(t)]
        personal_tasks = [t for t in tasks if not self._is_work_task(t)]

        # Generate narrative recap
        recap_prompt = f"""
        Generate a personalized weekly recap for a user based on their schedule.

        Week: {week_start.strftime('%B %d')} - {(week_start + timedelta(days=7)).strftime('%B %d, %Y')}

        Total tasks planned: {total_planned}
        Total tasks completed: {total_completed}
        Completion rate: {completion_rate:.0%}

        Work tasks: {len(work_tasks)} (completed: {len([t for t in work_tasks if t.status == 'completed'])})
        Personal tasks: {len(personal_tasks)} (completed: {len([t for t in personal_tasks if t.status == 'completed'])})

        Task breakdown:
        {self._format_tasks_for_prompt(tasks)}

        Generate:
        1. A warm, encouraging summary (2-3 paragraphs)
        2. Top 3 achievements this week
        3. Areas for improvement (if any)
        4. Recommendations for next week
        5. Work-life balance score (0-10)

        Tone: Supportive, insightful, motivational but realistic.
        """

        recap = self.llm.invoke(recap_prompt)

        # Save to database
        self._save_recap(user_id, week_start, completion_rate, recap)

        return recap
```

---

## 5. LangGraph Orchestration

### Workflow Graph

```python
from langgraph.graph import StateGraph, END

def create_scheduler_graph():
    workflow = StateGraph(AgentState)

    # Add nodes (agents)
    workflow.add_node("decomposer", TaskDecomposerAgent().decompose)
    workflow.add_node("scheduler_brain", SchedulerBrainAgent().schedule)
    workflow.add_node("ask_user", ask_user_for_conflict_resolution)
    workflow.add_node("calendar_integrator", CalendarIntegratorAgent().integrate)

    # Define edges
    workflow.add_edge("decomposer", "scheduler_brain")

    # Conditional edge: if conflicts need user input
    workflow.add_conditional_edges(
        "scheduler_brain",
        lambda state: "ask_user" if state["needs_user_input"] else "calendar_integrator",
        {
            "ask_user": "ask_user",
            "calendar_integrator": "calendar_integrator"
        }
    )

    workflow.add_edge("ask_user", "scheduler_brain")  # Loop back after user input
    workflow.add_edge("calendar_integrator", END)

    # Set entry point
    workflow.set_entry_point("decomposer")

    return workflow.compile()

# Usage
scheduler_graph = create_scheduler_graph()

# Run the workflow
result = scheduler_graph.invoke({
    "user_id": "user-123",
    "raw_transcript": "I need to finish the pitch deck by EOD...",
    "session_id": "session-456",
    "user_preferences": {...},
    "needs_user_input": False
})
```

---

## 6. Calendar & Email Integration

### Google Calendar API

**Setup:**
1. Create project in Google Cloud Console
2. Enable Google Calendar API and Gmail API
3. Create OAuth 2.0 credentials
4. Implement OAuth flow for users

**Key Operations:**
- `events().list()` - Fetch existing events
- `events().insert()` - Create new events
- `events().update()` - Modify events
- `events().delete()` - Remove events
- Use `sync_token` for incremental sync

**Code Example:**
```python
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

def get_google_calendar_service(user):
    credentials = Credentials.from_authorized_user_info(
        info=json.loads(user.google_calendar_token)
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

def sync_calendar_events(user_id):
    """Sync Google Calendar events to local DB"""
    service = get_google_calendar_service(user)

    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    for event in events:
        # Upsert to calendar_events table
        save_or_update_calendar_event(user_id, event)
```

### Gmail API

**Key Operations:**
- `messages().list()` - List emails with filters
- `messages().get()` - Get email content
- `messages().modify()` - Mark as read
- Use webhooks (Cloud Pub/Sub) for real-time notifications (advanced)

---

## 7. Data Flow & Execution Flow

### User Scheduling Request Flow

```
1. USER speaks/types request
   ↓
2. FRONTEND sends transcript to /api/schedule endpoint
   ↓
3. FASTAPI creates session, initializes AgentState
   ↓
4. LANGGRAPH executes:
   a. Agent 1 (Decomposer) → parses tasks
   b. Agent 2 (Scheduler Brain) → plans schedule, checks conflicts
   c. [CONDITIONAL] If conflicts → ask user → loop back to Agent 2
   d. Agent 3 (Calendar Integrator) → writes to Google Calendar
   ↓
5. BACKEND returns scheduled tasks + calendar links
   ↓
6. FRONTEND displays confirmation
```

### Email Tracking Flow (Background)

```
1. CELERY BEAT triggers email_tracker task every 30 minutes
   ↓
2. AGENT 4 (Email Tracker):
   a. Fetches new emails via Gmail API
   b. LLM extracts deadlines/tasks
   c. Creates tasks in DB
   d. Triggers Agent 2 (Scheduler Brain) if immediate scheduling needed
   ↓
3. If new tasks created → notify user (optional)
```

### Weekly Recap Flow (Background)

```
1. CELERY BEAT triggers weekly_recap task (Sunday 8 PM)
   ↓
2. AGENT 5 (Recap Generator):
   a. Fetches week's tasks and events
   b. Calculates metrics
   c. Generates narrative with LLM
   d. Saves to weekly_recaps table
   ↓
3. Email recap to user (optional)
   ↓
4. Display in app dashboard
```

---

## 8. API Design

### FastAPI Endpoints

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

class ScheduleRequest(BaseModel):
    user_id: str
    transcript: str

class ConflictResolution(BaseModel):
    session_id: str
    resolution: str  # "reschedule_existing" or "skip_new_task"
    selected_alternative: Optional[int]

@app.post("/api/schedule")
async def schedule_tasks(request: ScheduleRequest):
    """Main scheduling endpoint"""
    state = {
        "user_id": request.user_id,
        "raw_transcript": request.transcript,
        "session_id": generate_session_id(),
        "user_preferences": get_user_preferences(request.user_id),
        "needs_user_input": False
    }

    result = scheduler_graph.invoke(state)

    if result["needs_user_input"]:
        # Return conflicts for user to resolve
        return {
            "status": "needs_input",
            "conflicts": result["conflicts"],
            "session_id": result["session_id"]
        }

    return {
        "status": "success",
        "scheduled_tasks": result["scheduling_plan"],
        "calendar_event_ids": result["scheduled_events"]
    }

@app.post("/api/resolve-conflict")
async def resolve_conflict(resolution: ConflictResolution):
    """Handle user's conflict resolution"""
    # Resume LangGraph execution with user feedback
    state = get_session_state(resolution.session_id)
    state["user_feedback"] = resolution.resolution
    state["needs_user_input"] = False

    result = scheduler_graph.invoke(state)

    return {
        "status": "success",
        "scheduled_tasks": result["scheduling_plan"]
    }

@app.get("/api/tasks")
async def get_tasks(user_id: str, date: Optional[str] = None):
    """Get user's tasks"""
    # Query database
    pass

@app.get("/api/recap/{week_start}")
async def get_weekly_recap(user_id: str, week_start: str):
    """Get weekly recap"""
    # Query weekly_recaps table
    pass

@app.post("/api/auth/google")
async def google_oauth_callback(code: str):
    """Handle Google OAuth callback"""
    # Exchange code for tokens
    # Save to user table
    pass
```

---

## 9. Context Management Strategy

### The Challenge
Each agent needs access to:
- User's full calendar
- Current task list
- User preferences
- Conversation history
- Previous agent outputs

### Solution: Multi-Layered Context

1. **LangGraph State** (Hot Context)
   - Passed between agents in real-time
   - Contains current session data

2. **PostgreSQL** (Persistent Context)
   - Tasks, calendar events, user preferences
   - Queried on-demand by agents

3. **ChromaDB** (Historical Context)
   - Embeddings of past schedules, user behavior patterns
   - Used for RAG to inform scheduling decisions

   Example:
   ```python
   # When scheduling, retrieve similar past situations
   similar_patterns = chroma_db.query(
       query_text=f"User wants to schedule {task_description}",
       n_results=5
   )

   # Use patterns to inform current scheduling
   context_for_llm = f"""
   Based on past behavior:
   {similar_patterns}

   Current request:
   {current_task}
   """
   ```

4. **Redis Cache** (Fast Access)
   - Cache user preferences
   - Cache calendar availability matrix
   - TTL: 5-15 minutes

---

## 10. Deployment Architecture

### Docker Compose Setup

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/scheduler
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=scheduler
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/scheduler
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis

  celery_beat:
    build: .
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/scheduler
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

---

## 11. Implementation Roadmap (Hackathon Timeline)

### Day 1: Foundation (8 hours)
- [ ] Set up project structure
- [ ] Initialize FastAPI backend
- [ ] Set up PostgreSQL + migrations (use Alembic)
- [ ] Implement Google OAuth flow
- [ ] Create basic frontend (voice input + display)
- [ ] Test OpenAI API connection

### Day 2: Core Agents (10 hours)
- [ ] Implement Agent 1 (Task Decomposer)
- [ ] Implement Agent 2 (Scheduler Brain - basic version)
- [ ] Set up LangGraph orchestration
- [ ] Google Calendar integration (read + write)
- [ ] Test end-to-end scheduling flow

### Day 3: Advanced Features (8 hours)
- [ ] Implement conflict detection in Agent 2
- [ ] Add user conflict resolution flow
- [ ] Implement Agent 4 (Email Tracker) - basic version
- [ ] Set up Celery for background tasks
- [ ] Test email-to-task flow

### Day 4: Polish & Deploy (8 hours)
- [ ] Implement Agent 5 (Recap Generator)
- [ ] Frontend polish
- [ ] Error handling & logging
- [ ] Docker Compose setup
- [ ] Deploy to VM
- [ ] Integration testing
- [ ] Prepare demo

---

## 12. Key Design Decisions

### Why LangGraph over CrewAI?
- **State Management**: Built-in persistent state across agent invocations
- **Conditional Logic**: Easy to implement "if conflicts, ask user" flows
- **Debugging**: Better visibility into agent decision paths
- **Control**: More granular control over agent execution

### Why PostgreSQL over MongoDB?
- **ACID Compliance**: Critical for scheduling (no double bookings)
- **JSONB**: Still get flexibility for metadata
- **Relational**: Tasks, calendar events, users have clear relationships

### Why Google Calendar over Custom?
- **Ubiquity**: Most users already have Google Calendar
- **Robust API**: Well-documented, reliable
- **Cross-platform**: Works on web, mobile, desktop
- **Shared Calendars**: Can handle inviting others (Agent 2 feature)

### Why Modular Monolith over Microservices?
- **Hackathon Speed**: Faster to develop and debug
- **Shared State**: Agents need to share context frequently
- **Deployment Simplicity**: Single Docker container for main app
- **Migration Path**: Can split into microservices later if needed

---

## 13. Security Considerations

1. **OAuth Tokens**: Store encrypted in database (use `cryptography` library)
2. **API Keys**: Use environment variables, never commit to git
3. **User Data**: Implement row-level security (RLS) in PostgreSQL
4. **Rate Limiting**: Use FastAPI middleware to prevent abuse
5. **Input Validation**: Validate all user inputs (Pydantic models)

---

## 14. Monitoring & Observability

- **Logging**: Use `structlog` for structured logs
- **Metrics**: Track agent execution times, success rates
- **Errors**: Sentry integration for error tracking
- **Health Checks**: `/health` endpoint for monitoring

---

## 15. MVP vs. Future Enhancements

### MVP (Hackathon)
✅ Voice/text input scheduling
✅ Task decomposition
✅ Conflict detection
✅ Google Calendar integration
✅ Email tracking (basic)
✅ Weekly recap

### Future Enhancements
- 🔮 Multi-calendar support (work + personal)
- 🔮 Smart rescheduling (optimize entire week)
- 🔮 Habit tracking integration
- 🔮 Team scheduling (coordinate with others)
- 🔮 Energy-based scheduling (schedule hard tasks when user is most productive)
- 🔮 Mobile app
- 🔮 Slack/Teams integration

---

## 16. Testing Strategy

- **Unit Tests**: Test each agent's core logic
- **Integration Tests**: Test LangGraph workflows
- **API Tests**: Test FastAPI endpoints
- **E2E Tests**: Simulate full user journey
- Use `pytest` + `pytest-asyncio`

---

## Conclusion

This architecture balances hackathon speed with production-ready patterns. The modular design allows you to build incrementally, test frequently, and pivot if needed.

**Next Steps:**
1. Review this architecture
2. Set up development environment
3. Follow implementation roadmap
4. Build, test, iterate

Good luck with your hackathon! 🚀
