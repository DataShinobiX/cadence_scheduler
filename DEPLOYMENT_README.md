# UniGames Intelligent Scheduler - VM Deployment Guide

## 🎯 Quick Start (For Hackathon Judges & Reviewers)

**Live Demo**: http://95.179.179.94

### What This Application Does

UniGames Intelligent Scheduler is an AI-powered task management system that:
- ✅ **Voice-Activated Scheduling**: Speak naturally to create tasks
- ✅ **AI-Powered Optimization**: Multi-agent system finds optimal time slots
- ✅ **Email Intelligence**: Automatically extracts tasks from Gmail
- ✅ **Google Calendar Sync**: Seamlessly integrates with your calendar
- ✅ **Conflict Resolution**: Smart handling of scheduling conflicts with transparent AI reasoning

### Technology Stack

**Backend:**
- FastAPI (Python 3.10)
- PostgreSQL (Database)
- Redis (Cache/Message Broker)
- Celery (Background Tasks)
- LangGraph (Multi-Agent Orchestration)
- OpenAI GPT-4 (AI Scheduling Brain)
- OpenAI Whisper (Voice Transcription)

**Frontend:**
- React + Vite
- Tailwind CSS
- Modern animations & gradients

**Infrastructure:**
- Docker (PostgreSQL + Redis)
- Nginx (Reverse Proxy)
- Supervisor (Process Management)

---

## 📋 For Deployment Team

### VM Access Details

```
Host: 95.179.179.94
Username: root
Password: K5v-n]r=n6RTK$Re
SSH Command: ssh root@95.179.179.94
```

### Pre-Deployment Requirements

**1. API Keys Needed:**

| Service | Purpose | Where to Get | Required? |
|---------|---------|--------------|-----------|
| OpenAI API | Task scheduling (GPT-4) + Voice transcription (Whisper) | https://platform.openai.com/api-keys | ✅ Yes |
| Google OAuth | Calendar & Gmail integration | https://console.cloud.google.com/ | ✅ Yes |

**2. Google OAuth Setup:**

1. Go to: https://console.cloud.google.com/
2. Create project or use existing
3. Enable APIs:
   - Google Calendar API
   - Gmail API
4. Create OAuth 2.0 Client ID (Web application)
5. **IMPORTANT**: Add authorized redirect URI:
   ```
   http://95.179.179.94:8000/api/v1/auth/callback
   ```
6. Copy `Client ID` and `Client Secret`

**3. Update .env File:**

```bash
# Copy production template
cp .env.production .env

# Edit with your credentials
nano .env

# Set these values:
OPENAI_API_KEY=sk-your-actual-key-here
GOOGLE_CLIENT_ID=your-actual-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-secret
GOOGLE_REDIRECT_URI=http://95.179.179.94:8000/api/v1/auth/callback
SECRET_KEY=generate-random-secure-key
```

### Deployment Steps (Simple 3-Step Process)

#### Step 1: Check System Health (Local Machine)

```bash
# Run health check script
chmod +x check_system_health.sh
./check_system_health.sh
```

This validates:
- ✅ All environment variables are set
- ✅ Docker is running
- ✅ Database schema is ready
- ✅ All dependencies installed
- ✅ Scripts are executable

#### Step 2: Deploy to VM (Local Machine)

```bash
# Run deployment script
chmod +x deploy_to_vm.sh
./deploy_to_vm.sh
```

This will:
1. Test SSH connection to VM
2. Validate .env file
3. Create deployment package (excludes node_modules, venv, etc.)
4. Upload to VM
5. Install system dependencies (Docker, Node.js, Python, Nginx, etc.)
6. Extract application files to `/opt/unigames`

#### Step 3: Setup Production Environment (On VM)

```bash
# SSH into VM
ssh root@95.179.179.94

# Navigate to app directory
cd /opt/unigames

# Run production setup
chmod +x vm_setup_production.sh
./vm_setup_production.sh
```

This will:
1. Update .env for production settings
2. Create Python virtual environment
3. Install Python dependencies
4. Start Docker containers (PostgreSQL + Redis)
5. Create database schema (8 tables)
6. Setup authentication tables
7. Build frontend (React production bundle)
8. Configure Nginx (reverse proxy)
9. Setup Supervisor (process management)
10. Start all services:
    - FastAPI backend (4 workers on port 8000)
    - Celery worker (background tasks)
    - Celery beat (email agent scheduler - runs every 60 seconds)
    - Nginx (port 80)

**Expected Output:**
```
========================================
Production Setup Complete!
========================================

Service URLs:
  - Frontend:  http://95.179.179.94
  - API:       http://95.179.179.94/api
  - API Docs:  http://95.179.179.94/api/docs
```

---

## 🔍 Verification & Testing

### 1. Check All Services Are Running

```bash
# On VM
supervisorctl status unigames:*
```

**Expected:**
```
unigames:unigames-backend          RUNNING   pid 1234, uptime 0:05:00
unigames:unigames-celery-beat      RUNNING   pid 1235, uptime 0:05:00
unigames:unigames-celery-worker    RUNNING   pid 1236, uptime 0:05:00
```

### 2. Test Application in Browser

#### Frontend: http://95.179.179.94
- Should see login/signup page
- Modern UI with gradients and animations

#### API Docs: http://95.179.179.94/api/docs
- Interactive API documentation
- Can test endpoints

#### Health Check: http://95.179.179.94/api/health
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T12:00:00Z"
}
```

### 3. Test Core Features

**A. User Registration & Login**
1. Click "Sign Up"
2. Enter email and password
3. Should redirect to dashboard

**B. Google OAuth**
1. Click "Connect Google Calendar"
2. OAuth flow should work
3. Should see success message

**C. Voice Scheduling**
1. Click microphone icon
2. Record: "Schedule a meeting tomorrow at 3pm"
3. Should see:
   - Transcription appears
   - Agent thinking flow animation
   - Task created
   - Calendar event created
   - Success notification

**D. Email Agent**
1. Send email to your connected Gmail account with task-like content:
   ```
   Subject: Team Meeting
   Body: Let's meet on Monday at 2pm to discuss the project
   ```
2. Wait 60 seconds (Celery beat schedule)
3. Check tasks - should auto-create from email

**E. Conflict Resolution**
1. Record: "Schedule gym after 5pm today"
2. If no slots available today, should see:
   - Yellow conflict card
   - AI Analysis box with reasoning
   - Suggestion to adjust constraints
   - No error or crash

---

## 📊 Monitoring & Logs

### View Logs

```bash
# All logs
tail -f /var/log/unigames/*.log

# Backend only
tail -f /var/log/unigames/backend.log

# Celery worker (email agent)
tail -f /var/log/unigames/celery-worker.log

# Celery beat (scheduler)
tail -f /var/log/unigames/celery-beat.log

# Nginx access
tail -f /var/log/nginx/access.log

# Nginx errors
tail -f /var/log/nginx/error.log
```

### Service Management

```bash
# Restart all services
supervisorctl restart unigames:*

# Restart specific service
supervisorctl restart unigames:unigames-backend
supervisorctl restart unigames:unigames-celery-worker
supervisorctl restart unigames:unigames-celery-beat

# Stop all
supervisorctl stop unigames:*

# Start all
supervisorctl start unigames:*

# View detailed status
supervisorctl status
```

### Database Access

```bash
# PostgreSQL CLI
docker exec -it unigames-postgres psql -U scheduler_user -d scheduler_db

# Check tables
\dt

# Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM calendar_events;
SELECT COUNT(*) FROM email_tracking;

# View recent tasks
SELECT id, title, created_at FROM tasks ORDER BY created_at DESC LIMIT 10;
```

### Redis Monitoring

```bash
# Redis CLI
docker exec -it unigames-redis redis-cli

# Check keys
KEYS *

# Monitor real-time commands
MONITOR

# Check Celery queue
LLEN celery
```

---

## 🎯 Architecture Overview

### Multi-Agent System Flow

```
1. USER VOICE INPUT
   ↓
2. AGENT 1: Transcription (OpenAI Whisper)
   → Converts speech to text
   ↓
3. AGENT 2: Task Decomposition (GPT-4)
   → Extracts tasks, deadlines, priorities
   → Breaks down into actionable items
   ↓
4. AGENT 3: Scheduler Brain (GPT-4 + LangGraph)
   → Finds optimal time slots
   → Handles conflicts intelligently
   → Returns reasoning for decisions
   ↓
5. AGENT 4: Calendar Integration (Google Calendar API)
   → Creates calendar events
   → Syncs with Google Calendar
   ↓
6. RESULT DISPLAYED TO USER
   ✅ Success: Green cards with scheduled tasks
   ⚠️  Conflicts: Yellow cards with AI reasoning
```

### Email Agent (Background Service)

```
CELERY BEAT (Scheduler)
   → Triggers every 60 seconds
   ↓
CELERY WORKER
   → Fetches emails from Gmail API
   → Extracts task-like content using GPT-4
   → Checks for duplicates (by gmail_message_id)
   → Creates tasks in database
   → Schedules using multi-agent system
   → Creates calendar events
```

### Database Schema (8 Tables)

1. **users** - User accounts
2. **google_tokens** - OAuth tokens for Google API
3. **tasks** - All tasks (voice + email)
4. **calendar_events** - Google Calendar events
5. **task_calendar_mapping** - Links tasks to events
6. **user_preferences** - User settings
7. **email_tracking** - Processed emails (prevents duplicates)
8. **celery_task_meta** - Celery task status

### Infrastructure Services

| Service | Port | Purpose | Managed By |
|---------|------|---------|------------|
| Nginx | 80 | Reverse proxy + Static files | systemd |
| FastAPI | 8000 | Backend API | Supervisor |
| PostgreSQL | 5432 | Database | Docker |
| Redis | 6379 | Cache + Message broker | Docker |
| Celery Worker | - | Background tasks | Supervisor |
| Celery Beat | - | Task scheduler | Supervisor |
| React Frontend | - | UI (built to static files) | Nginx |

---

## 🛠️ Troubleshooting

### Issue: "Cannot connect to VM"

**Solution:**
```bash
# Test connection
ping 95.179.179.94

# Try SSH with verbose output
ssh -v root@95.179.179.94

# Check if password is correct
# Password: K5v-n]r=n6RTK$Re
```

### Issue: "Services not starting"

**Check logs:**
```bash
supervisorctl tail unigames:unigames-backend
supervisorctl tail unigames:unigames-celery-worker
```

**Common fixes:**
```bash
# Restart services
supervisorctl restart unigames:*

# Restart Docker
docker-compose restart

# Check database is ready
docker exec unigames-postgres pg_isready
```

### Issue: "Database connection failed"

**Solution:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -c "SELECT 1;"

# Check credentials in .env
cat .env | grep DATABASE_URL

# Restart PostgreSQL
docker restart unigames-postgres
sleep 10
supervisorctl restart unigames:*
```

### Issue: "Email agent not processing emails"

**Check:**
```bash
# Is Celery worker running?
supervisorctl status unigames:unigames-celery-worker

# Is Celery beat running?
supervisorctl status unigames:unigames-celery-beat

# Check logs
tail -f /var/log/unigames/celery-*.log

# Restart email services
supervisorctl restart unigames:unigames-celery-worker
supervisorctl restart unigames:unigames-celery-beat
```

### Issue: "Frontend shows 404"

**Solution:**
```bash
# Check Nginx is running
systemctl status nginx

# Test Nginx config
nginx -t

# Check frontend build exists
ls -la /opt/unigames/frontend/dist

# Rebuild frontend
cd /opt/unigames/frontend
npm run build
systemctl reload nginx
```

### Issue: "API returns 502 Bad Gateway"

**Solution:**
```bash
# Check backend is running
supervisorctl status unigames:unigames-backend

# Check backend logs
tail -f /var/log/unigames/backend.log

# Restart backend
supervisorctl restart unigames:unigames-backend

# Check port 8000 is listening
netstat -tlnp | grep 8000
```

### Issue: "Google OAuth fails"

**Solution:**
1. Check redirect URI in Google Console:
   - Should be: `http://95.179.179.94:8000/api/v1/auth/callback`
2. Check .env:
   ```bash
   grep GOOGLE_REDIRECT_URI /opt/unigames/.env
   ```
3. Ensure Google Calendar API and Gmail API are enabled
4. Check OAuth consent screen is configured

---

## 📁 File Structure (On VM)

```
/opt/unigames/
├── app/                          # Backend application
│   ├── agents/                   # Agent implementations
│   │   ├── task_decomposer.py   # Agent 1: Task extraction
│   │   ├── scheduler_brain.py   # Agent 2: Scheduling logic
│   │   └── calendar_integrator.py  # Agent 3: Google Calendar
│   ├── orchestration/           # LangGraph workflow
│   │   ├── scheduler_graph.py   # Multi-agent orchestration
│   │   ├── state.py             # Shared state definition
│   │   └── agent_adapters.py    # Agent interfaces
│   ├── routes/                   # API endpoints
│   ├── services/                 # Business logic
│   ├── database/                 # Database models & setup
│   ├── celery_app.py            # Celery configuration
│   └── main.py                   # FastAPI app entry point
├── frontend/                     # React application
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   └── services/            # API clients
│   └── dist/                    # Production build (created by setup)
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker services config
├── setup_database.sh             # Database schema setup
├── setup_auth_db.sh              # Auth tables setup
├── run_backend.sh                # Local backend start
├── run_celery_worker.sh          # Local celery worker
├── run_celery_beat.sh            # Local celery beat
├── start_email_agent.sh          # Local email agent
└── vm_setup_production.sh        # Production setup script

/var/log/unigames/               # Application logs
├── backend.log
├── backend-error.log
├── celery-worker.log
├── celery-worker-error.log
├── celery-beat.log
└── celery-beat-error.log

/etc/supervisor/conf.d/
└── unigames.conf                # Supervisor process config

/etc/nginx/sites-available/
└── unigames                     # Nginx site config
```

---

## 🎓 Key Features Implemented

### 1. Voice-Activated Scheduling
- OpenAI Whisper for speech-to-text
- Natural language processing
- Real-time transcription display

### 2. Multi-Agent Orchestration
- LangGraph workflow engine
- State management between agents
- Graceful error handling
- Max retry logic for conflicts

### 3. Intelligent Conflict Resolution
- LLM explains why tasks can't be scheduled
- Transparent AI reasoning shown to users
- Suggestions for constraint adjustment
- No crashes on conflicts

### 4. Email Intelligence
- Automated Gmail monitoring (every 60 seconds)
- Task extraction from emails
- Duplicate prevention via message ID
- Automatic scheduling and calendar creation

### 5. Modern UI/UX
- Agent thinking flow visualization
- Toast notifications
- Reminders history tab
- Smooth animations and gradients
- Responsive design

### 6. Production-Ready Infrastructure
- Supervisor for process management
- Nginx reverse proxy
- Docker for databases
- Comprehensive logging
- Health check endpoints

---

## 📞 Support & Documentation

### Documentation Files

1. **DEPLOYMENT_README.md** (this file) - Main deployment guide
2. **PRE_DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist
3. **VM_DEPLOYMENT_QUICK_REFERENCE.md** - Quick commands reference
4. **UNIGAMES_VM_DEPLOYMENT_GUIDE.md** - Comprehensive technical guide
5. **SCHEDULER_CONFLICT_FIXES.md** - Conflict resolution documentation
6. **REMINDERS_TAB.md** - Reminders feature documentation

### Quick Commands Reference

```bash
# Check system status
supervisorctl status

# Restart everything
supervisorctl restart unigames:*

# View all logs
tail -f /var/log/unigames/*.log

# Database access
docker exec -it unigames-postgres psql -U scheduler_user -d scheduler_db

# Redis access
docker exec -it unigames-redis redis-cli

# Check containers
docker ps

# Restart Docker services
docker-compose restart

# Reload Nginx
systemctl reload nginx

# Check disk space
df -h

# Check memory
free -h

# Check processes
ps aux | grep python
ps aux | grep celery
```

---

## ✅ Success Metrics

After deployment, verify:

- [ ] Application accessible at http://95.179.179.94
- [ ] All 3 Supervisor processes running (backend, celery-worker, celery-beat)
- [ ] PostgreSQL and Redis containers running
- [ ] Nginx serving frontend and proxying API
- [ ] Users can sign up and log in
- [ ] Google OAuth flow works
- [ ] Voice recording creates tasks
- [ ] Tasks are scheduled without errors
- [ ] Calendar events created in Google Calendar
- [ ] Email agent processes emails every 60 seconds
- [ ] Conflict resolution shows AI reasoning
- [ ] No errors in logs
- [ ] API docs accessible at /api/docs

---

## 🚀 Final Notes

This application demonstrates:

✅ **Advanced AI Integration**: Multi-agent system with GPT-4 for intelligent scheduling
✅ **Production Infrastructure**: Docker, Supervisor, Nginx, proper process management
✅ **Modern Frontend**: React with smooth animations and great UX
✅ **Background Processing**: Celery for email monitoring and task automation
✅ **Robust Error Handling**: Graceful degradation, conflict resolution, transparent AI reasoning
✅ **Complete Documentation**: Comprehensive guides for deployment and troubleshooting

**Deployment Time**: ~15 minutes (including build)
**Uptime Target**: 99%+
**Performance**: 4 workers, optimized for concurrent requests

---

**Last Updated**: November 2025
**For**: Hackathon Submission
**Team**: UniGames Intelligent Scheduler
**VM**: 95.179.179.94

Good luck with the hackathon! 🎉
