# 🎯 UniGames Intelligent Scheduler - Demo Guide for Judges

## 📋 Quick Demo Credentials

**To test the application, use these credentials:**

```
Email: paritoshsingh1612@gmail.com
Login Method: Passwordless (click "Login" - no password needed)
```

## 🚀 What This Demo Shows

This is a **fully functional multi-agent AI scheduler** with real Google Calendar and Gmail integration.

### Key Features:

1. **🎤 Voice-Based Task Scheduling**
   - Record your voice: "Schedule a meeting with Bob tomorrow at 3pm"
   - AI transcribes, understands, and schedules automatically
   - Events appear in **real Google Calendar**

2. **🤖 Multi-Agent AI System (4 Agents)**
   - **Agent 1**: Speech-to-Text (Whisper API)
   - **Agent 2**: Task Decomposition (extracts tasks from natural language)
   - **Agent 3**: Intelligent Scheduling Brain (finds optimal time slots)
   - **Agent 4**: Calendar Integration (creates Google Calendar events)

3. **📅 Live Google Calendar View**
   - See real calendar events from paritoshsingh1612@gmail.com
   - All scheduled tasks appear here in real-time

4. **📧 Automatic Email Task Extraction**
   - Background agent reads Gmail every 60 seconds
   - Extracts actionable tasks from emails using LLM
   - Automatically schedules them in calendar

5. **🔔 Intelligent Notifications**
   - Upcoming event reminders
   - Weekly highlights summary
   - AI-generated insights

## 🎬 How to Demo (Step-by-Step)

### Step 1: Access the Application

```
Production URL: http://95.179.179.94
Local Dev: http://localhost:5173
```

### Step 2: Login

1. Click "Login" tab
2. Enter email: `paritoshsingh1612@gmail.com`
3. Click "Login" (no password required)

### Step 3: Test Voice Scheduling

1. Click the **microphone button** on dashboard
2. Say something like:
   - "Schedule a demo presentation tomorrow at 2pm"
   - "Add lunch meeting with the team on Friday at noon"
   - "Create a reminder to submit the report next Monday"
3. Watch the AI agents process your request (you'll see their thinking!)
4. The event is automatically created in Google Calendar

### Step 4: View Calendar

1. Click "Calendar" tab
2. You'll see all events from the real Google Calendar
3. Any tasks you just scheduled will appear here

### Step 5: Check Notifications

1. Click "Notifications" tab
2. See upcoming events and weekly highlights
3. AI-generated summaries and insights

## 🔐 Architecture Highlights

### Multi-User Ready

- Each user can connect their own Google account
- Tokens stored securely in PostgreSQL database
- Automatic token refresh (no re-authentication needed)
- Complete data isolation between users

### Real Google Integration

- **NOT a mock** - uses real Google Calendar API
- **NOT a simulation** - creates actual calendar events
- Events scheduled during demo will appear in paritoshsingh1612@gmail.com's Google Calendar

### LangGraph Multi-Agent Orchestration

```
User Voice Input
     ↓
[Agent 1: Transcription] → Whisper API
     ↓
[Agent 2: Task Decomposition] → GPT-4 extracts tasks
     ↓
[Agent 3: Scheduler Brain] → Intelligent time allocation
     ↓
[Agent 4: Calendar Integration] → Google Calendar API
     ↓
Event Created ✅
```

### Background Email Agent

```
Celery Beat (every 60 seconds)
     ↓
Read Gmail API (unread emails)
     ↓
LLM extracts actionable tasks
     ↓
Auto-schedule in calendar
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Multi-agent orchestration
- **PostgreSQL** - User data and token storage
- **Redis** - Task queue and caching
- **Celery** - Background task processing
- **OpenAI GPT-4** - Natural language understanding
- **Whisper API** - Speech-to-text transcription
- **Google Calendar API** - Calendar integration
- **Gmail API** - Email reading

### Frontend
- **React** - UI framework
- **Vite** - Fast build tool
- **Tailwind CSS** - Styling
- **Web Audio API** - Voice recording

### DevOps
- **Docker** (optional) - Containerization
- **Nginx** - Reverse proxy (production)
- **Systemd** - Service management (production)

## 🎯 What Makes This Special

### 1. Real AI Multi-Agent System
- Not just API calls - true agent collaboration
- Each agent has specialized role and autonomy
- Agents communicate through shared state (LangGraph)

### 2. Production-Ready OAuth
- Automatic token refresh
- Multi-user support
- Secure token storage
- No manual re-authentication needed

### 3. Intelligent Scheduling
- Considers existing calendar events
- Respects work hours and lunch breaks
- Finds optimal time slots
- Handles conflicts gracefully

### 4. Email Intelligence
- Understands natural language in emails
- Extracts deadlines and tasks
- Auto-schedules without user intervention

## 📊 Demo Scenarios

### Scenario 1: Quick Task Scheduling
**Say**: "Schedule a code review tomorrow at 10am"
**Result**: Event created in Google Calendar for tomorrow at 10:00 AM

### Scenario 2: Complex Multi-Task
**Say**: "I need to finish the project report by Friday, review the codebase on Thursday, and meet with the team on Wednesday"
**Result**: 3 separate tasks extracted and scheduled optimally

### Scenario 3: Natural Language Understanding
**Say**: "Remind me to call mom this weekend"
**Result**: AI understands "this weekend" and schedules for Saturday

### Scenario 4: Email-to-Calendar (Background)
**Setup**: Send email to paritoshsingh1612@gmail.com with task mention
**Result**: Within 60 seconds, task automatically appears in calendar

## ⚠️ Important Notes for Judges

### What You're Seeing is Real

- When you schedule a task during the demo, it **actually creates an event** in paritoshsingh1612@gmail.com's Google Calendar
- You can verify this by checking the Calendar tab - it shows real Google Calendar data
- The email agent is actually reading real Gmail messages

### Why We Use a Pre-Configured Account

For hackathon demo purposes, we're using a single demo account so judges can:
- ✅ Test immediately without OAuth setup
- ✅ See working integration without connecting personal Google accounts
- ✅ Focus on features rather than authentication

### Multi-User Capability

The system **fully supports** multiple users:
- New users can connect their own Google accounts
- Each user sees only their own data
- Complete OAuth 2.0 implementation included
- See `JUDGES_GOOGLE_OAUTH_GUIDE.md` for multi-user architecture

## 🔧 Setup Instructions (For VM Deployment)

### Prerequisites on VM

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql redis-server nginx

# Create database
sudo -u postgres psql -c "CREATE DATABASE scheduler_db;"
sudo -u postgres psql -c "CREATE USER scheduler_user WITH PASSWORD 'scheduler_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE scheduler_db TO scheduler_user;"
```

### Deploy Application

```bash
# Clone or upload code to VM
cd /opt/unigames

# Setup backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.production .env
# Edit .env with your OpenAI API key and Google OAuth credentials

# Run database migrations
alembic upgrade head

# Setup demo user
python setup_demo_user.py

# Start services
./vm_setup_production.sh
```

### Start Backend Services

```bash
# FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Celery worker (for email agent)
celery -A app.tasks.celery_app worker --loglevel=info

# Celery beat (scheduler for periodic tasks)
celery -A app.tasks.celery_app beat --loglevel=info
```

### Start Frontend

```bash
cd frontend
npm install
npm run build
# Serve with nginx or: npm run preview -- --host 0.0.0.0 --port 80
```

## 🎓 Educational Value

This project demonstrates:

1. **Modern AI/ML Integration**
   - LLM-based task understanding
   - Speech recognition (Whisper)
   - Multi-agent coordination (LangGraph)

2. **Production Software Engineering**
   - OAuth 2.0 implementation
   - Database design (PostgreSQL)
   - Background task processing (Celery)
   - RESTful API design (FastAPI)
   - Modern frontend (React)

3. **Cloud/DevOps**
   - VM deployment
   - Service management
   - Database administration
   - API integration

## 📞 Support

If you encounter any issues during the demo:

1. Check that all services are running:
   ```bash
   # Backend
   curl http://localhost:8000/

   # Database
   psql postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db -c "SELECT 1;"

   # Redis
   redis-cli ping
   ```

2. Verify demo user is configured:
   ```bash
   python setup_demo_user.py
   ```

3. Check logs:
   ```bash
   # Backend logs
   tail -f logs/app.log

   # Celery logs
   tail -f logs/celery.log
   ```

## 🎉 Summary

**UniGames Intelligent Scheduler** is a production-ready, AI-powered scheduling assistant that:

- ✅ Uses real Google Calendar and Gmail APIs
- ✅ Implements sophisticated multi-agent AI system
- ✅ Supports voice-based natural language input
- ✅ Automatically extracts tasks from emails
- ✅ Provides intelligent scheduling with conflict resolution
- ✅ Offers beautiful, responsive UI
- ✅ Is fully multi-user capable
- ✅ Deployed and accessible on public VM

---

**Demo URL**: http://95.179.179.94
**Demo Email**: paritoshsingh1612@gmail.com
**Demo Method**: Passwordless login

**Thank you for reviewing our project!** 🚀
