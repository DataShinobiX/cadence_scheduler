# UniGames VM Deployment - Quick Reference

## One-Page Architecture Summary

**Application**: Intelligent Scheduler (AI-powered calendar & email management)

**Tech Stack**: FastAPI (Python) + React (JavaScript) + PostgreSQL + Redis + Celery

**All Services Required**: Backend, Frontend, Database, Cache, 2x Background Task Processors

---

## Service Checklist (Must All Run)

```
┌─ Infrastructure (Docker Container)
│  ├─ PostgreSQL:5432 (Database)
│  ├─ Redis:6379 (Cache + Message Broker)
│  └─ pgAdmin:5050 (Optional - Database UI)
│
├─ Backend (Python, Port 8000)
│  └─ FastAPI with Uvicorn
│
├─ Email Agent (Background, No Port)
│  ├─ Celery Worker (processes tasks)
│  └─ Celery Beat (schedules every 1 minute)
│
└─ Frontend (React, Port 5173 dev / 3000 prod)
   └─ Vite Build Tool
```

---

## Startup Sequence (Order Matters!)

### 1. Docker Services (Infrastructure)
```bash
docker-compose up -d
# Starts: PostgreSQL, Redis, optional pgAdmin
# Initializes: Database schema from scripts/init_db.sql
# Wait: 10-15 seconds for database to be ready
```

### 2. Celery Worker
```bash
celery -A app.celery_app worker --pool=solo --loglevel=info &
# Processes: Background tasks from Redis queue
# Requires: Redis running, Python dependencies installed
```

### 3. Celery Beat
```bash
celery -A app.celery_app beat --loglevel=info &
# Schedules: Email check every 60 seconds
# Requires: Redis running
```

### 4. FastAPI Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Serves: REST API endpoints
# Requires: Database connection, Redis access
```

### 5. Frontend (Development)
```bash
cd frontend && npm run dev
# Development server: http://localhost:5173
# Hot reload on code changes
```

**For Production Frontend**:
```bash
cd frontend && npm run build
# Generates: frontend/dist/ (static files)
# Serve via: Nginx or web server
```

---

## Service Dependency Map

```
User Browser
     ↓
   React UI (localhost:5173)
     ↓
FastAPI Backend (localhost:8000)
     ↓
     ├─→ PostgreSQL (localhost:5432)
     │   └─ All data: users, tasks, calendar, emails
     │
     ├─→ Redis (localhost:6379)
     │   └─ Task queue, cache, Celery broker
     │
     ├─→ Google Calendar API
     │   └─ Sync scheduled events
     │
     └─→ Celery Worker (Background)
         └─→ Celery Beat (Scheduler)
             └─→ Email Agent Task (every 60 sec)
                 ├─ Read Gmail
                 ├─ Extract tasks via OpenAI
                 ├─ Save to Database
                 └─ Prevent duplicates via gmail_message_id
```

---

## Critical Files Location Map

| What | Location | Purpose |
|------|----------|---------|
| Backend entry | `app/main.py` | FastAPI app definition |
| Celery config | `app/celery_app.py` | Task queue + Beat schedule |
| Email agent | `app/tasks/email_checker.py` | Email extraction task |
| Email logic | `app/agents/email_tracking.py` | LLM-powered email parsing |
| Startup scripts | `run_backend.sh`, `run_celery_*.sh` | Quick start commands |
| Database schema | `scripts/init_db.sql` | Auto-creates all tables |
| Environment | `.env.example` → `.env` | Configuration (API keys) |
| Docker | `docker-compose.yml` | Infrastructure definition |
| Frontend | `frontend/src/` | React code |
| Frontend build | `frontend/package.json` | Dependencies & build |

---

## Database Tables (8 Total)

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `users` | User accounts | user_id, email, preferences, google_tokens |
| `tasks` | AI-decomposed tasks | task_id, user_id, description, status, deadline |
| `calendar_events` | Google Calendar sync | event_id, google_event_id, start/end times |
| `email_tracking` | Gmail tracking | gmail_message_id (unique!), processed flag |
| `agent_context` | LLM execution logs | session_id, agent_name, context_data |
| `weekly_recaps` | Productivity summaries | week_start/end, completion_rate |
| `scheduling_conflicts` | Conflict detection | conflict_type, resolution_status |
| `user_sessions` | Session management | session_id, current_state |

**Key**: Email deduplication via unique `gmail_message_id` in `email_tracking` table

---

## External APIs Required

| API | Purpose | Credential | Where |
|-----|---------|-----------|-------|
| **Google Calendar** | Schedule events | OAuth token | User account |
| **Google Gmail** | Read emails | OAuth token | Same as above |
| **OpenAI (GPT-4)** | Task decomposition | API Key | `.env` |
| **OpenAI (Whisper)** | Audio transcription | API Key | `.env` |
| **OpenAI (Custom)** | Email extraction | API Key | `app/api/transcribe.py` (hardcoded!) |

**Note**: OpenAI credentials hardcoded in `app/api/transcribe.py` should be moved to `.env`

---

## Environment Variables (Minimal Set)

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scheduler_db
DB_USER=scheduler_user
DB_PASSWORD=scheduler_pass

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Google APIs
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
```

---

## Running Commands

### Local Development
```bash
# Terminal 1: Docker services
docker-compose up -d

# Terminal 2: Backend
./run_backend.sh

# Terminal 3: Frontend
cd frontend && npm run dev

# Terminal 4: Email Agent
./start_email_agent.sh
```

### VM Deployment
```bash
# (Assuming systemd units or supervisor config)
systemctl start docker-compose
systemctl start unigames-backend
systemctl start unigames-celery-worker
systemctl start unigames-celery-beat
systemctl start unigames-frontend
```

---

## Email Agent Details

**Runs**: Every 60 seconds (via Celery Beat)

**Flow**:
1. Check Gmail for recent emails (via `SimpleEmailSchedulerAdapter`)
2. Use LLM to extract actionable items (deadlines, meetings, etc.)
3. Save extracted tasks to `tasks` table
4. Mark email as processed in `email_tracking` table
5. Create calendar events if scheduling enabled

**Database Tracking**:
- `email_tracking.gmail_message_id` = unique Gmail ID (prevents re-processing)
- `email_tracking.processed` = boolean flag
- `email_tracking.task_id` = links to created task

**Credentials Required**:
- `credentials.json` (Google OAuth)
- `token.json` (Generated on first auth)

---

## Logs to Monitor

| Log | Command | What To Watch |
|-----|---------|---------------|
| Backend | `tail -f backend.log` | API errors, startup issues |
| Celery Worker | `tail -f celery-worker.log` | Task execution errors |
| Celery Beat | `tail -f celery-beat.log` | Schedule triggers (every 60 sec) |
| Docker | `docker-compose logs -f` | Container startup, crashes |
| Database | `docker-compose logs db` | Connection errors |

**Health Checks**:
```bash
# Backend responsive?
curl http://localhost:8000/docs

# Database connected?
psql -h localhost -U scheduler_user -d scheduler_db -c "SELECT 1"

# Redis responsive?
redis-cli ping

# Celery worker alive?
celery -A app.celery_app inspect active
```

---

## Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| SIGSEGV crash | Celery worker dies immediately | Use `--pool=solo` (already done) |
| Email agent not running | Celery Beat running but no emails extracted | Check `credentials.json`, `token.json` exist |
| Duplicate tasks | Same email processed multiple times | `email_tracking.gmail_message_id` not unique |
| No calendar sync | Events not in Google Calendar | Check Google OAuth token not expired |
| DB connection pool full | "too many connections" errors | Increase `DATABASE_POOL_SIZE` |
| Frontend CORS error | "Access-Control-Allow-Origin" error | Check CORS in `app/main.py` |

---

## Ports Overview

| Service | Port | Type | Access |
|---------|------|------|--------|
| Frontend | 5173 | HTTP | http://localhost:5173 |
| Backend | 8000 | HTTP | http://localhost:8000 |
| API Docs | 8000/docs | HTTP | http://localhost:8000/docs |
| Database | 5432 | TCP | psql connection |
| Redis | 6379 | TCP | Internal only |
| pgAdmin | 5050 | HTTP | http://localhost:5050 (optional) |

---

## Scaling Notes

**For Production**:
- Run Backend via: `gunicorn app.main:app -w 4 -b 0.0.0.0:8000`
- Run Celery Worker via: `celery -A app.celery_app worker -c 4 --loglevel=info`
- Run Celery Beat: Only ONE instance (use Redis lock)
- Database: Connection pool size = (workers * 2) + 2
- Frontend: Serve static files from Nginx/CDN

**Not Multi-threaded Ready**:
- Current code uses `--pool=solo` due to OpenAI/LangChain conflicts
- For higher concurrency, test `--pool=prefork` and monitor for crashes

---

## Success Indicators

After deployment, you should see:

1. **Backend logs**: "Application startup complete"
2. **Celery Beat logs**: "scheduled check-emails-every-minute"
3. **Frontend**: React app loads at http://localhost:5173
4. **Database**: `psql -h localhost -U scheduler_user -d scheduler_db -c "SELECT COUNT(*) FROM users"`
5. **Email Agent**: Every 60 seconds in Celery logs, check email_tracking table for new rows

---

## One-Line Deploy Commands

### Install Everything
```bash
docker-compose up -d && pip install -r requirements.txt && cd frontend && npm install
```

### Start All Services
```bash
docker-compose up -d && nohup celery -A app.celery_app worker --pool=solo > celery-worker.log 2>&1 & nohup celery -A app.celery_app beat > celery-beat.log 2>&1 & nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 & cd frontend && npm run dev
```

### Stop All Services
```bash
pkill -f "celery|uvicorn"; docker-compose down
```

---

## Reference Files

**Full Deployment Guide**: `UNIGAMES_VM_DEPLOYMENT_GUIDE.md` (comprehensive, 500+ lines)

**This File**: `VM_DEPLOYMENT_QUICK_REFERENCE.md` (quick lookup, this file)

**Original Docs**:
- `README.md` - Project overview
- `SETUP_FOR_COLLABORATORS.md` - Local development
- `DATABASE_SETUP_README.md` - Database details
