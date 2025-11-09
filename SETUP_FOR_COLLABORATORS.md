# Setup Guide for Collaborators

This guide will help you set up the UniGames Intelligent Scheduler on your local machine.

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ and npm installed
- Python 3.11+ installed
- Git

## 🚀 Quick Setup (5 minutes)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd unigames
```

### Step 2: Start Docker Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis
- pgAdmin (optional database viewer)

**Wait 10 seconds** for the database to initialize.

### Step 3: Set Up Authentication Database

Run this script to create the required auth tables:

```bash
./setup_auth_db.sh
```

You should see:
```
✅ Authentication Database Setup Complete!
```

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

**Important**: Add your Google Calendar API credentials to `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scheduler_db
DB_USER=scheduler_user
DB_PASSWORD=scheduler_pass

# Google Calendar API (REQUIRED - Ask project owner for these)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# OpenAI API (REQUIRED - Ask project owner for this)
OPENAI_API_KEY=your_openai_api_key_here

# Redis
REDIS_URL=redis://localhost:6379
```

### Step 6: Start the Backend

```bash
./run_backend.sh
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Start the Frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

### Step 8: Test the Application

1. Visit: http://localhost:5173
2. You should see the **Login/Signup page**
3. Click **Sign Up**
4. Enter:
   - Email: `your-email@example.com`
   - Name: `Your Name`
5. Click **Sign Up**
6. You'll be redirected to the dashboard!

---

## 🔧 Troubleshooting

### Issue: "404 Not Found" on Signup

**Cause**: Authentication database tables not set up

**Solution**:
```bash
./setup_auth_db.sh
```

### Issue: Docker containers not running

**Check containers**:
```bash
docker ps
```

You should see 3 containers:
- `unigames-db-1` (PostgreSQL)
- `scheduler_redis` (Redis)
- `scheduler_pgadmin` (pgAdmin)

**Restart containers**:
```bash
docker-compose down
docker-compose up -d
```

### Issue: "Connection refused" to database

**Check database is running**:
```bash
docker exec -i unigames-db-1 psql -U scheduler_user -d scheduler_db -c "SELECT 1;"
```

Should output: `1`

### Issue: Backend won't start - "Module not found"

**Reinstall dependencies**:
```bash
pip install -r requirements.txt
```

### Issue: Frontend shows blank page

**Check browser console** for errors

**Verify backend is running**:
```bash
curl http://localhost:8000/
```

Should return JSON with API info

### Issue: "OPENAI_API_KEY not found"

**Ask the project owner** for the API key and add it to `.env`:
```env
OPENAI_API_KEY=sk-proj-...
```

---

## 📊 Verify Database Setup

Check if auth tables exist:

```bash
docker exec -i unigames-db-1 psql -U scheduler_user -d scheduler_db -c "\dt"
```

You should see:
- `users`
- `auth_sessions`
- `tasks`
- `calendar_events`
- And other tables...

Check auth_sessions table structure:

```bash
docker exec -i unigames-db-1 psql -U scheduler_user -d scheduler_db -c "\d auth_sessions"
```

---

## 🧪 Test Authentication Flow

### Via Browser:
1. Visit http://localhost:5173
2. Sign up with a new email
3. Record a voice command
4. See tasks scheduled!

### Via Command Line:

**Signup**:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

Expected response:
```json
{
  "session_token": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "...",
  "user": {
    "email": "test@example.com",
    "name": "Test User",
    ...
  }
}
```

**Login**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Get Current User** (replace TOKEN):
```bash
TOKEN="your-session-token-here"
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📁 Project Structure

```
unigames/
├── app/                      # Backend Python code
│   ├── api/                 # API endpoints
│   │   ├── auth.py         # Authentication endpoints
│   │   └── transcribe.py   # Voice transcription
│   ├── agents/             # AI agents
│   ├── orchestration/      # Agent workflow
│   └── middleware/         # Auth middleware
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── context/       # AuthContext
│   │   ├── pages/         # Auth, Dashboard, etc.
│   │   └── utils/         # API utilities
│   └── package.json
├── docker-compose.yml      # Database services
├── setup_auth_db.sh       # Auth setup script
├── run_backend.sh         # Backend start script
└── requirements.txt       # Python dependencies
```

---

## 🎯 Key Features Implemented

### Authentication System
- ✅ Email-based signup (no password for hackathon)
- ✅ Session token management (7-day expiry)
- ✅ Protected routes (must login to access)
- ✅ Automatic logout on session expiry

### Voice Assistant
- ✅ Record voice commands
- ✅ AI transcription (OpenAI Whisper)
- ✅ Task decomposition (Agent 1)
- ✅ Intelligent scheduling (Agent 2)
- ✅ Google Calendar integration (Agent 3)

### Multi-User Support
- ✅ Each user has their own account
- ✅ Each user has their own calendar
- ✅ Each user has their own tasks
- ✅ No data sharing between users

---

## 🔑 Important Files

### Backend
- `app/api/auth.py` - Authentication endpoints
- `app/middleware/auth.py` - Auth validation
- `app/api/transcribe.py` - Voice processing (requires auth)
- `app/orchestration/orchestrator.py` - Agent workflow

### Frontend
- `src/context/AuthContext.jsx` - Global auth state
- `src/pages/Auth.jsx` - Login/Signup page
- `src/components/ProtectedRoute.jsx` - Route protection
- `src/utils/api.js` - Authenticated API calls

### Database
- `setup_auth_db.sh` - Creates auth_sessions table

---

## 🚨 Common First-Time Setup Issues

### 1. Missing environment variables
Create `.env` file and ask project owner for API keys

### 2. Database not initialized
Run `./setup_auth_db.sh`

### 3. Docker not running
Start Docker Desktop, then run `docker-compose up -d`

### 4. Port conflicts
If port 8000 or 5173 is in use, kill the process:
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 💡 Development Tips

### Backend Development
- Backend runs on: http://localhost:8000
- API docs: http://localhost:8000/docs
- Logs appear in terminal where you ran `./run_backend.sh`

### Frontend Development
- Frontend runs on: http://localhost:5173
- Hot reload enabled (changes appear instantly)
- React DevTools recommended

### Database Access
- pgAdmin: http://localhost:5050
  - Email: `admin@admin.com`
  - Password: `admin`
- Connect to server:
  - Host: `postgres` (from Docker) or `localhost` (from host)
  - Port: `5432`
  - Database: `scheduler_db`
  - Username: `scheduler_user`
  - Password: `scheduler_pass`

---

## 📞 Getting Help

1. **Check logs**: Backend terminal shows detailed error messages
2. **Check browser console**: Frontend errors appear in DevTools
3. **Run setup script**: `./setup_auth_db.sh` fixes most auth issues
4. **Ask project owner**: For API keys and credentials

---

## ✅ Setup Checklist

- [ ] Docker Desktop installed and running
- [ ] `docker-compose up -d` completed successfully
- [ ] `./setup_auth_db.sh` ran successfully
- [ ] `.env` file created with API keys
- [ ] `pip install -r requirements.txt` completed
- [ ] Backend starts: `./run_backend.sh`
- [ ] Frontend starts: `cd frontend && npm run dev`
- [ ] Can signup at http://localhost:5173
- [ ] Can record voice and see tasks scheduled

---

**Once all checkboxes are complete, you're ready to develop! 🎉**
