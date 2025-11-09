# UniGames Application - Complete Deployment Guide for VM

## Executive Summary

The UniGames Intelligent Scheduler is a multi-agent AI application that intelligently manages calendars, extracts deadlines from emails, and provides productivity insights. It consists of:

- **Backend**: FastAPI (Python) with multiple AI agents orchestrated via LangGraph
- **Frontend**: React + Vite (TypeScript/JavaScript)
- **Database**: PostgreSQL 15
- **Cache/Message Queue**: Redis
- **Background Tasks**: Celery + Celery Beat
- **Email Agent**: Automated task extraction from Gmail

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│                    Port 5173 (Vite Dev)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│            Port 8000 (Uvicorn ASGI Server)                   │
├─────────────────────────────────────────────────────────────┤
│  API Routes:                                                 │
│  - /api/auth/*           (Authentication)                    │
│  - /api/transcribe       (Audio → Scheduling)                │
│  - /api/calendar/*       (Google Calendar Integration)       │
│  - /api/notifications/*  (Event Notifications)               │
└──────┬──────────────────────────┬──────────────────────────┬─┘
       │                          │                          │
       ▼                          ▼                          ▼
┌─────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  PostgreSQL     │  │     Redis          │  │  Google APIs       │
│  Port 5432      │  │   Port 6379        │  │  (Calendar, Gmail) │
│  (Tasks, Users, │  │  (Celery Broker,   │  │                    │
│   Calendar,     │  │   Result Backend)  │  │                    │
│   Email Data)   │  │                    │  │                    │
└─────────────────┘  └────────────────────┘  └────────────────────┘
       ▲                          ▲
       └──────────────┬───────────┘
                      │
    ┌─────────────────┴─────────────────┐
    │                                   │
    ▼                                   ▼
┌──────────────────────┐    ┌──────────────────────┐
│  Celery Worker       │    │  Celery Beat         │
│  Port: None          │    │  Port: None          │
│  (Processes Tasks)   │    │  (Schedules Tasks    │
│  Pool: solo          │    │   Every 1 Minute)    │
└──────────────────────┘    └──────────────────────┘
         │
         └─────────────────────────┬──────────────────┐
                                   │                  │
                    ┌──────────────▼─────┐    ┌──────▼─────────┐
                    │ Email Agent Task   │    │ Email Tracking │
                    │ (check_emails_and  │    │ Database       │
                    │  _schedule)        │    │ (gmail_message │
                    │ Runs every 1 min   │    │  _id tracking) │
                    └────────────────────┘    └────────────────┘
```

---

## Current Local Setup

### 1. How Application is Currently Started Locally

#### **Step 1: Start Database & Redis (Docker)**
```bash
docker-compose up -d
# Starts:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - pgAdmin (port 5050, optional)
```

#### **Step 2: Backend Server**
```bash
./run_backend.sh
# Runs: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Auto-reloads on code changes
# Available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

#### **Step 3: Frontend Development Server**
```bash
cd frontend
npm install  # First time only
npm run dev
# Runs Vite dev server at http://localhost:5173
```

#### **Step 4: Email Agent (Celery Worker + Beat)**
```bash
# Option A: Run separately in terminals
./run_celery_worker.sh    # Terminal 1
./run_celery_beat.sh      # Terminal 2

# Option B: Run together in background
./start_email_agent.sh    # Starts both in background
./stop_email_agent.sh     # Stops both
```

---

## Complete Service Architecture

### Services That Need to Run

#### **1. PostgreSQL Database** (Essential)
- **Port**: 5432
- **Container Name**: `scheduler_db` (via docker-compose)
- **Credentials**:
  - User: `scheduler_user`
  - Password: `scheduler_pass`
  - Database: `scheduler_db`
- **Initialization**: `scripts/init_db.sql` (auto-runs on startup)
- **Tables Created**:
  - `users` - User accounts and preferences
  - `tasks` - Task records (AI-decomposed)
  - `calendar_events` - Google Calendar sync
  - `email_tracking` - Gmail message tracking
  - `agent_context` - Agent execution logs
  - `weekly_recaps` - Productivity summaries
  - `scheduling_conflicts` - Conflict detection
  - `user_sessions` - Session management

#### **2. Redis** (Essential for Celery)
- **Port**: 6379
- **Container Name**: `scheduler_redis` (via docker-compose)
- **Purpose**: 
  - Celery task broker (message queue)
  - Celery result backend (task results storage)
- **Configuration in app/celery_app.py**:
  ```python
  broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
  backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
  ```

#### **3. FastAPI Backend** (Essential)
- **Port**: 8000
- **Entry Point**: `app/main.py`
- **Server**: Uvicorn ASGI
- **Key Routes**:
  - `POST /api/auth/signup` - User registration
  - `POST /api/auth/login` - User login
  - `GET /api/auth/me` - Current user info
  - `POST /api/transcribe` - Main orchestration endpoint
  - `GET /api/calendar/events` - Get calendar events
  - `GET /api/notifications` - Get notifications
  - `GET /api/notifications/highlights` - Weekly recap

#### **4. Celery Worker** (Essential for Background Tasks)
- **Type**: Background task processor
- **Pool**: `solo` (no forking - fixes SIGSEGV with OpenAI/LangChain)
- **Log Level**: info
- **Broker**: Redis (localhost:6379)
- **Task Module**: `app.tasks.email_checker`
- **Key Tasks**:
  - `app.tasks.email_checker.check_emails_and_schedule` (runs every minute)
  - `app.tasks.email_checker.test_email_agent`

#### **5. Celery Beat Scheduler** (Essential for Periodic Tasks)
- **Type**: Periodic task scheduler
- **Schedule**:
  ```python
  beat_schedule = {
      'check-emails-every-minute': {
          'task': 'app.tasks.email_checker.check_emails_and_schedule',
          'schedule': 60.0,  # 1 minute in seconds
          'expires': 55,
      }
  }
  ```
- **Purpose**: Triggers email checking every 1 minute
- **Broker**: Redis

#### **6. Email Agent / Email Tracking**
- **Type**: Celery task (executed by Worker)
- **Frequency**: Every 1 minute (via Celery Beat)
- **Implementation**: `app/tasks/email_checker.py`
- **Agent Logic**: `app/agents/email_tracking.py`
- **Features**:
  - Reads unread emails from Gmail (API)
  - Uses LLM to extract actionable items
  - Saves extracted tasks to database
  - Marks emails as processed (avoids duplicates)
  - Triggers scheduling for extracted tasks
- **Database Tracking**:
  - `email_tracking` table stores:
    - `gmail_message_id` (prevents duplicates)
    - `subject`, `sender`, `received_at`
    - `processed` flag
    - `task_id` (foreign key to created task)

#### **7. React Frontend** (Development)
- **Port**: 5173
- **Build Tool**: Vite
- **Entry Point**: `frontend/src/index.html`
- **Build Command**: `npm run build`
- **Output**: `frontend/dist/` (static files)
- **Dependencies**: React Router, Axios, Tailwind CSS, Headless UI

---

## Database Setup & Schema

### Initialization Script: `scripts/init_db.sql`

**Automatically runs when PostgreSQL container starts**

#### Tables Created:

1. **users**
   - user_id (UUID, PK)
   - email (unique)
   - name, timezone
   - google_calendar_token, gmail_token (OAuth)
   - preferences (JSONB)
   - onboarding_completed, created_at, updated_at

2. **tasks**
   - task_id (UUID, PK)
   - user_id (FK)
   - description, original_input
   - task_type (user_requested | email_derived | decomposed | recurring)
   - priority (1-10)
   - status (pending | scheduled | in_progress | completed | cancelled | blocked)
   - scheduled_date, start_time, duration_minutes
   - deadline, location, attendees (JSONB)
   - tags, metadata
   - created_at, updated_at, completed_at

3. **calendar_events**
   - event_id (UUID, PK)
   - user_id (FK)
   - google_event_id (unique external ID)
   - task_id (FK - links to created task)
   - summary, description, location
   - start_datetime, end_datetime (must satisfy end > start)
   - attendees, organizer
   - is_external, is_movable, is_all_day
   - recurrence_rule
   - sync_status (synced | pending | failed | conflict)
   - last_synced_at

4. **email_tracking**
   - email_id (UUID, PK)
   - user_id (FK)
   - gmail_message_id (unique - for duplicate prevention)
   - gmail_thread_id
   - subject, sender, sender_email
   - received_at
   - extracted_deadline, extracted_task_description
   - extracted_priority, extracted_location
   - extraction_confidence (0-1)
   - processed (boolean)
   - processed_at (timestamp)
   - task_id (FK - links to created task)
   - metadata (JSONB)

5. **agent_context**
   - context_id (UUID, PK)
   - user_id (FK), session_id
   - agent_name, agent_version
   - context_type (input | output | state | error | debug)
   - context_data (JSONB)
   - execution_time_ms, tokens_used
   - created_at

6. **weekly_recaps**
   - recap_id (UUID, PK)
   - user_id (FK)
   - week_start_date, week_end_date
   - total_tasks_planned, total_tasks_completed
   - completion_rate, productivity_score, work_life_balance_score
   - work_tasks_completed, personal_tasks_completed, health_tasks_completed
   - summary, recommendations, highlights (JSONB)
   - most_productive_day, most_productive_time
   - common_postponed_tasks

7. **scheduling_conflicts**
   - conflict_id (UUID, PK)
   - user_id (FK), session_id
   - conflict_type (time_overlap | travel_time_insufficient | preference_violation | double_booking | deadline_impossible)
   - task_id (FK), conflicting_event_id (FK)
   - resolution_status (pending | resolved | ignored | auto_resolved)
   - resolution_chosen, alternatives_offered (JSONB)
   - resolved_at, created_at

8. **user_sessions**
   - session_id (string, PK)
   - user_id (FK)
   - session_type (scheduling | recap_view | settings | conflict_resolution | email_sync)
   - current_state (JSONB)
   - is_active, started_at, last_activity_at, ended_at

#### Indexes Created (16 total):
- User lookups by email
- Task queries by user/status/date
- Calendar event range queries
- Email tracking by message ID (prevents duplicates)
- Agent context by session
- Conflict resolution queries
- Session activity tracking

#### Triggers:
- Auto-update `updated_at` timestamps on table changes

#### Views:
- `upcoming_tasks` - Pending/scheduled tasks ordered by priority
- `todays_schedule` - Today's calendar events with linked tasks

---

## External Service Dependencies

### 1. Google Calendar API
- **Purpose**: Sync scheduled events to user's Google Calendar
- **Requires**: OAuth 2.0 credentials
- **Credentials File**: `credentials.json` (in project root)
- **Token File**: `token.json` (generated on first auth)
- **Environment Variables**:
  ```
  GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=your-client-secret
  GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
  ```
- **Scopes**: Google Calendar API, Gmail API (read-only)

### 2. Gmail API
- **Purpose**: Extract deadlines and tasks from emails
- **Credentials**: Same as Google Calendar (via service account)
- **Scopes**: `https://www.googleapis.com/auth/gmail.readonly`
- **Implementation**: `app/agents/email_tracking.py` → `SimpleEmailSchedulerAdapter` class

### 3. OpenAI API
- **Purpose**: LLM for task decomposition, scheduling, email analysis
- **Models Used**:
  - `gpt-4` - Main scheduling decisions
  - `gpt-5-mini` - (via custom API endpoint) Email extraction
- **Environment Variable**:
  ```
  OPENAI_API_KEY=sk-...
  OPENAI_MODEL=gpt-4
  OPENAI_TEMPERATURE=0.0
  ```
- **Hardcoded in transcribe.py** (should be moved to .env):
  ```python
  API_KEY = "sk-aU7KLAifP85EWxg4J7NFJg"
  BASE_URL = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
  ```

---

## Python Dependencies & Requirements

**File**: `requirements.txt`

### Core Framework
- `fastapi==0.109.0` - Web framework
- `uvicorn[standard]==0.27.0` - ASGI server
- `python-multipart==0.0.6` - File upload handling

### Database
- `sqlalchemy==2.0.25` - ORM (though using raw SQL via psycopg2)
- `alembic==1.13.1` - Database migrations
- `asyncpg==0.29.0` - Async PostgreSQL
- `psycopg2-binary==2.9.x` - PostgreSQL driver (implied)

### AI & Agents
- `openai==1.10.0` - OpenAI API client
- `langchain==0.1.0` - LLM framework
- `langchain-openai==0.0.2` - OpenAI integration
- `langgraph==0.0.20` - Agent orchestration framework

### Google APIs
- `google-auth==2.27.0` - Google authentication
- `google-auth-oauthlib==1.2.0` - OAuth flow
- `google-auth-httplib2==0.2.0` - HTTP transport
- `google-api-python-client==2.115.0` - Google API client library

### Background Tasks
- `celery==5.3.6` - Task queue
- `redis==5.0.1` - Redis client & cache

### Security & Auth
- `pydantic==2.5.3` - Data validation
- `pydantic-settings==2.1.0` - Settings management
- `python-jose[cryptography]==3.3.0` - JWT handling
- `passlib[bcrypt]==1.7.4` - Password hashing
- `email-validator==2.3.0` - Email validation
- `httpx==0.26.0` - HTTP client

### Utilities
- `python-dotenv==1.0.0` - .env loading
- `structlog==24.1.0` - Structured logging
- `beautifulsoup4==4.12.3` - HTML parsing (email extraction)

### Testing & Development
- `pytest==7.4.4` - Testing framework
- `pytest-asyncio==0.23.3` - Async test support
- `black==24.1.1` - Code formatter
- `ruff==0.1.14` - Linter

---

## Environment Variables & Configuration

**File**: `.env.example` → `.env`

### Application Settings
```env
APP_NAME=Intelligent Scheduler
DEBUG=true
SECRET_KEY=change-this-to-a-random-secret-key-in-production
```

### Database Configuration
```env
DATABASE_URL=postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db
DATABASE_POOL_SIZE=5
# OR individual components:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scheduler_db
DB_USER=scheduler_user
DB_PASSWORD=scheduler_pass
```

### Redis Configuration
```env
REDIS_URL=redis://localhost:6379/0
```

### OpenAI Configuration
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.0
```

### Google OAuth & APIs
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

### JWT & Security
```env
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Celery Configuration
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Optional Email Settings
```env
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
```

### Development Settings
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
RELOAD=true
WORKERS=1
RATE_LIMIT_PER_MINUTE=60
DEFAULT_TIMEZONE=UTC
```

---

## Frontend Build Configuration

**File**: `frontend/package.json`

### Build Scripts
```json
{
  "scripts": {
    "dev": "vite",                    // Development server (port 5173)
    "build": "vite build",            // Production build
    "preview": "vite preview"         // Preview production build
  }
}
```

### Build Configuration: `frontend/vite.config.js`
```javascript
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist'                    // Output directory for production
  },
  server: {
    port: 5173,
    open: true,
    fs: { allow: ['.'] }
  },
  appType: 'spa'                      // Single-page application
});
```

### Key Dependencies
- `react` (implicit dependency via @vitejs/plugin-react)
- `react-router-dom==7.9.5` - Routing
- `@headlessui/react==2.2.9` - UI components
- `@heroicons/react==2.2.0` - Icons
- `tailwindcss==3.4.14` - Styling
- `axios==1.13.2` - HTTP client
- `vite==7.2.2` - Build tool
- `postcss==8.5.6`, `autoprefixer==10.4.21` - CSS processing

### Production Build Process
1. Install dependencies: `npm install`
2. Build: `npm run build` → generates `frontend/dist/`
3. Serve static files from backend or separate web server

---

## Deployment Strategy for VM

### Phase 1: Pre-Deployment Checklist

- [ ] VM specification (Ubuntu 22.04 LTS recommended)
- [ ] Python 3.11+ installed
- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL 15 (via Docker or native)
- [ ] Redis (via Docker or native)
- [ ] Node.js 18+ (for frontend build)
- [ ] PM2 or systemd for process management
- [ ] Nginx or Apache for reverse proxy
- [ ] SSL certificates (Let's Encrypt)
- [ ] Environment variables configured
- [ ] External API keys configured

### Phase 2: Service Startup Order (Critical)

```bash
# 1. Start infrastructure services (Docker)
docker-compose up -d

# 2. Wait for database to be ready
sleep 10

# 3. Start Celery Worker (background task processor)
nohup celery -A app.celery_app worker --loglevel=info --pool=solo > celery-worker.log 2>&1 &

# 4. Start Celery Beat (periodic task scheduler)
nohup celery -A app.celery_app beat --loglevel=info > celery-beat.log 2>&1 &

# 5. Start FastAPI backend
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 6. Frontend (either serve static or run dev)
# For production: serve frontend/dist/ from Nginx
# For development: npm run dev
```

### Phase 3: Monitoring & Logging

**Log Files to Monitor**:
- `celery-worker.log` - Background task execution
- `celery-beat.log` - Periodic task scheduling
- `backend.log` - FastAPI errors
- Docker logs: `docker-compose logs -f`

**Key Metrics to Monitor**:
- Celery worker CPU/memory (email checking every 1 minute)
- Database connection pool usage
- Redis memory usage
- Backend API response times
- Email extraction success rate

### Phase 4: Scaling Considerations

- **Celery Worker**: Can run multiple workers with pool=prefork (instead of solo)
- **Celery Beat**: Should run only ONE instance (use Redis for lock)
- **FastAPI**: Can run multiple workers behind load balancer
- **Database**: PostgreSQL should handle 1M+ emails easily
- **Redis**: Single instance sufficient for most workloads

---

## Complete Service Dependency Graph

```
┌─────────────────────────────────────────────────┐
│  Docker Compose (Orchestrates Infrastructure)   │
│  ├─ PostgreSQL 15 (Port 5432)                   │
│  ├─ Redis (Port 6379)                           │
│  └─ pgAdmin (Port 5050, optional)               │
└─────────────────────────────────────────────────┘
             ▲
             │
             │ (requires)
             │
┌─────────────────────────────────────────────────┐
│  FastAPI Backend (Port 8000)                    │
│  ├─ Requires: Database, Redis, Google APIs     │
│  ├─ Calls: Celery tasks via Redis              │
│  └─ Serves: REST API, WebSocket (optional)     │
└─────────────────────────────────────────────────┘
             ▲
             │
             │ (HTTP to)
             │
┌─────────────────────────────────────────────────┐
│  React Frontend (Port 5173 / 3000 prod)         │
│  ├─ Requires: FastAPI backend                  │
│  └─ Calls: /api/* endpoints                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Celery Worker (Background Task Processor)      │
│  ├─ Requires: Redis (broker), Database         │
│  ├─ Processes: Tasks from queue                │
│  ├─ Uses: OpenAI API, Google APIs              │
│  └─ Logs to: celery-worker.log                 │
└─────────────────────────────────────────────────┘
             ▲
             │
             │ (tasks via)
             │
┌─────────────────────────────────────────────────┐
│  Celery Beat (Periodic Task Scheduler)          │
│  ├─ Requires: Redis (broker)                   │
│  ├─ Schedules: check_emails_and_schedule       │
│  │            every 60 seconds                 │
│  └─ Logs to: celery-beat.log                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Email Agent Task (Celery Task)                 │
│  ├─ Implementation: app/tasks/email_checker.py │
│  ├─ Agent: app/agents/email_tracking.py        │
│  ├─ Frequency: Every 1 minute (via Beat)       │
│  ├─ Requires: Gmail credentials.json, token.json
│  ├─ Calls: Google Gmail API                    │
│  ├─ Calls: OpenAI API (LLM for extraction)    │
│  ├─ Stores: Tasks to Database                 │
│  └─ Tracking: email_tracking table             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  External Services                              │
│  ├─ OpenAI API (GPT-4, Whisper)                │
│  ├─ Google Calendar API                         │
│  ├─ Google Gmail API                            │
│  └─ (Optional) SMTP for notifications          │
└─────────────────────────────────────────────────┘
```

---

## Critical Files & Locations

### Startup Scripts
- `/run_backend.sh` - FastAPI startup
- `/run_celery_worker.sh` - Celery worker
- `/run_celery_beat.sh` - Celery beat
- `/start_email_agent.sh` - Both celery services
- `/stop_email_agent.sh` - Stop both services
- `/setup_database.sh` - Database initialization

### Configuration Files
- `/.env.example` → `/.env` - Environment variables
- `/docker-compose.yml` - Infrastructure services
- `/requirements.txt` - Python dependencies
- `/frontend/package.json` - Frontend dependencies
- `/frontend/vite.config.js` - Vite build config

### Python Application
- `/app/main.py` - FastAPI entry point
- `/app/celery_app.py` - Celery configuration & beat schedule
- `/app/config.py` - Application settings
- `/app/api/*` - REST API endpoints
- `/app/agents/*` - AI agent implementations
- `/app/tasks/email_checker.py` - Email background task
- `/app/orchestration/*` - LangGraph workflow

### Database
- `/scripts/init_db.sql` - Database initialization (auto-run)
- `/scripts/verify_database.py` - Database verification script

### Frontend
- `/frontend/src/` - React source code
- `/frontend/dist/` - Built static files (production)

### Credentials
- `/credentials.json` - Google OAuth credentials (gitignored)
- `/token.json` - Google OAuth token (auto-generated, gitignored)

### Logs
- `/celery-worker.log` - Celery worker logs
- `/celery-beat.log` - Celery beat logs
- `/celery-worker.pid`, `/celery-beat.pid` - Process IDs

---

## Production Deployment Checklist

### Infrastructure
- [ ] VM with 4GB+ RAM, 2+ CPU cores
- [ ] PostgreSQL 15 with automated backups
- [ ] Redis with persistence enabled
- [ ] Reverse proxy (Nginx/Apache)
- [ ] SSL/TLS certificates
- [ ] Firewall rules configured

### Application Setup
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables in `.env` (never commit to git!)
- [ ] Google OAuth credentials configured
- [ ] OpenAI API key configured

### Database
- [ ] PostgreSQL initialized with schema
- [ ] Backup strategy implemented
- [ ] Connection pooling configured
- [ ] Indexes verified

### Services
- [ ] FastAPI backend running (via gunicorn, not uvicorn)
- [ ] Celery worker running (with supervisor/systemd)
- [ ] Celery beat running (single instance, with lock)
- [ ] Frontend built and served (static files)
- [ ] All services have restart policies

### Monitoring
- [ ] Logging configured (syslog/ELK)
- [ ] Error tracking (Sentry/similar)
- [ ] Uptime monitoring
- [ ] Database monitoring
- [ ] Celery task monitoring

### Security
- [ ] Secrets management (not in .env on production)
- [ ] Database credentials encrypted
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation enforced

---

## Troubleshooting Common Issues

### 1. Celery Worker Crashes with SIGSEGV
**Cause**: Forking issues with OpenAI/LangChain libraries
**Solution**: Use `--pool=solo` flag (already done in scripts)

### 2. Email Agent Not Finding Credentials
**Solution**: Ensure `credentials.json` and `token.json` are in project root
```bash
ls credentials.json token.json
```

### 3. Database Connection Pool Exhausted
**Cause**: Too many concurrent tasks
**Solution**: Increase `DATABASE_POOL_SIZE` in .env, reduce Celery concurrency

### 4. Redis Connection Errors
**Solution**: Verify Redis is running
```bash
docker-compose ps
redis-cli ping
```

### 5. Frontend Can't Connect to Backend
**Cause**: CORS not configured properly
**Solution**: Check `app/main.py` CORS middleware, verify backend is running

### 6. Email Agent Skips All Emails
**Cause**: All emails already processed
**Solution**: Check `email_tracking` table for processed=true entries
```sql
SELECT COUNT(*) FROM email_tracking WHERE processed = true;
```

---

## Summary: Services to Deploy on VM

| Service | Type | Port | Startup Command | Log File | Critical? |
|---------|------|------|-----------------|----------|-----------|
| PostgreSQL | Container | 5432 | `docker-compose up -d db` | Docker logs | **YES** |
| Redis | Container | 6379 | `docker-compose up -d redis` | Docker logs | **YES** |
| FastAPI | Python | 8000 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | backend.log | **YES** |
| Celery Worker | Python | - | `celery -A app.celery_app worker --pool=solo --loglevel=info` | celery-worker.log | **YES** |
| Celery Beat | Python | - | `celery -A app.celery_app beat --loglevel=info` | celery-beat.log | **YES** |
| React Frontend | Static | 3000 | `npm run build && serve dist` | - | **YES** |
| pgAdmin | Container | 5050 | `docker-compose up -d pgadmin` | Docker logs | NO |

---

## Next Steps for VM Deployment

1. **Prepare VM**: Install Docker, Docker Compose, Python 3.11+, Node.js 18+
2. **Clone Repository**: Get latest code from git
3. **Configure Secrets**: Update `.env` with API keys and credentials
4. **Initialize Database**: Run `docker-compose up -d && setup_database.sh`
5. **Install Dependencies**: `pip install -r requirements.txt`, `cd frontend && npm install`
6. **Build Frontend**: `cd frontend && npm run build`
7. **Start Services**: Use systemd units or supervisor for process management
8. **Configure Nginx**: Reverse proxy to FastAPI (8000) and serve frontend
9. **Set Up Monitoring**: Configure logging, error tracking, uptime monitoring
10. **Test End-to-End**: Verify all services work, email agent triggers, calendar syncs

