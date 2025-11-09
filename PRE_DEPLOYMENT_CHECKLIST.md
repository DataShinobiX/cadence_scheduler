# Pre-Deployment Checklist for UniGames VM Deployment

## 🎯 Before Running `deploy_to_vm.sh`

### 1. Environment Variables Setup

**Critical API Keys Required:**

- [ ] **OpenAI API Key**
  - Get from: https://platform.openai.com/api-keys
  - Must have GPT-4 access (for scheduling logic)
  - Needs Whisper access (for voice transcription)
  - Set in `.env`: `OPENAI_API_KEY=sk-...`

- [ ] **Google OAuth Credentials**
  - Go to: https://console.cloud.google.com/
  - Create new project or use existing
  - Enable APIs:
    - ✅ Google Calendar API
    - ✅ Gmail API
  - Create OAuth 2.0 Client ID (Web application)
  - **IMPORTANT**: Add redirect URI: `http://95.179.179.94:8000/api/v1/auth/callback`
  - Copy credentials:
    - `GOOGLE_CLIENT_ID=...`
    - `GOOGLE_CLIENT_SECRET=...`
    - `GOOGLE_REDIRECT_URI=http://95.179.179.94:8000/api/v1/auth/callback`

- [ ] **Secret Key**
  - Generate a secure random key:
    ```bash
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
    ```
  - Set in `.env`: `SECRET_KEY=<generated-key>`

### 2. Verify .env File

```bash
# Check .env exists
ls -la .env

# Verify critical variables are set (not placeholder values)
grep -E "OPENAI_API_KEY|GOOGLE_CLIENT_ID|GOOGLE_CLIENT_SECRET" .env
```

**Make sure these are NOT placeholders:**
- ❌ `OPENAI_API_KEY=sk-your-openai-api-key-here`
- ❌ `GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com`
- ❌ `GOOGLE_CLIENT_SECRET=your-client-secret`

### 3. Test Local Application First

**Before deploying, verify everything works locally:**

```bash
# Terminal 1: Start infrastructure
docker-compose up -d

# Terminal 2: Setup database
./setup_database.sh
./setup_auth_db.sh

# Terminal 3: Start backend
./run_backend.sh

# Terminal 4: Start frontend
cd frontend && npm run dev

# Terminal 5: Start email agent
./start_email_agent.sh
```

**Test these features:**
- [ ] User can sign up and log in
- [ ] Google OAuth authentication works
- [ ] Voice recording and transcription works
- [ ] Task decomposition creates tasks
- [ ] Scheduler brain schedules tasks without errors
- [ ] Calendar integration creates events
- [ ] Email agent reads Gmail and extracts tasks
- [ ] No RecursionError or infinite loops on conflicts

### 4. Verify All Services Work

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check database connection
docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -c "SELECT COUNT(*) FROM users;"

# Check Redis
docker exec unigames-redis redis-cli ping

# Check Celery worker
# Should see tasks being processed in terminal

# Check frontend
# Open http://localhost:5173 in browser
```

### 5. Code Quality Checks

- [ ] No syntax errors in Python files
  ```bash
  python3 -m py_compile app/**/*.py
  ```

- [ ] Frontend builds without errors
  ```bash
  cd frontend && npm run build
  ```

- [ ] All shell scripts are executable
  ```bash
  chmod +x *.sh
  ```

### 6. Orchestrator Verification

**Critical fix completed:**
- [x] Added `conflict_resolution_attempts` and `show_conflicts_to_user` to `AgentState`
- [x] Fixed `workflow.compile()` TypeError
- [x] LLM reasoning captured and returned to frontend
- [x] Max retry counter prevents infinite loops

**Verify the fix:**
```bash
# Test with conflicting constraint
# Record: "Schedule gym after 5pm today"
# Should see conflict with LLM reasoning, not RecursionError
```

### 7. Database Schema Ready

**Verify all tables exist:**
```bash
docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -c "\dt"
```

**Should show 8 tables:**
1. users
2. google_tokens
3. tasks
4. calendar_events
5. task_calendar_mapping
6. user_preferences
7. email_tracking
8. celery_task_meta

### 8. Email Agent Configuration

**Verify Celery configuration:**
- [ ] `run_celery_worker.sh` exists and is executable
- [ ] `run_celery_beat.sh` exists and is executable
- [ ] `start_email_agent.sh` exists and is executable
- [ ] Beat schedule set to 60 seconds (checks Gmail every minute)

```bash
# Test email agent
./start_email_agent.sh

# Should see logs:
# - Celery worker started
# - Celery beat started
# - Email check task scheduled every 60 seconds
```

### 9. File Permissions

```bash
# Make all scripts executable
chmod +x *.sh
chmod +x deploy_to_vm.sh
chmod +x vm_setup_production.sh
```

### 10. Documentation Review

- [ ] Read `VM_DEPLOYMENT_QUICK_REFERENCE.md`
- [ ] Read `UNIGAMES_VM_DEPLOYMENT_GUIDE.md`
- [ ] Understand service dependencies
- [ ] Know how to check logs on VM

---

## 🚀 Ready to Deploy?

### Step-by-Step Deployment Process

#### 1. Deploy Application to VM
```bash
# From your local machine
chmod +x deploy_to_vm.sh
./deploy_to_vm.sh
```

This will:
- Test SSH connection
- Validate environment variables
- Create deployment package
- Upload to VM
- Install system dependencies
- Extract application files

#### 2. SSH into VM
```bash
ssh root@95.179.179.94
# Password: K5v-n]r=n6RTK$Re
```

#### 3. Navigate to Application
```bash
cd /opt/unigames
```

#### 4. Run Production Setup
```bash
chmod +x vm_setup_production.sh
./vm_setup_production.sh
```

This will:
- Configure environment for production
- Setup Python virtual environment
- Start Docker containers (PostgreSQL + Redis)
- Create database schema
- Setup authentication tables
- Build frontend
- Configure Nginx
- Setup Supervisor for process management
- Start all services:
  - FastAPI backend (4 workers)
  - Celery worker (background tasks)
  - Celery beat (email agent scheduler)
  - Nginx (web server)

#### 5. Verify Deployment

```bash
# Check all services are running
supervisorctl status unigames:*

# Expected output:
# unigames:unigames-backend          RUNNING   pid 1234, uptime 0:00:30
# unigames:unigames-celery-beat      RUNNING   pid 1235, uptime 0:00:30
# unigames:unigames-celery-worker    RUNNING   pid 1236, uptime 0:00:30

# Check Nginx
systemctl status nginx

# Check Docker containers
docker ps

# Should see:
# - unigames-postgres
# - unigames-redis
```

#### 6. Test Application

Open in browser:
- **Frontend**: http://95.179.179.94
- **API Docs**: http://95.179.179.94/api/docs
- **Health Check**: http://95.179.179.94/api/health

**Test flow:**
1. Sign up / Log in
2. Connect Google account (OAuth)
3. Record voice command: "Schedule a meeting tomorrow at 3pm"
4. Verify task is created
5. Check calendar integration
6. Send test email to Gmail
7. Wait 60 seconds for email agent to process
8. Verify task extracted from email

---

## 🔍 Post-Deployment Monitoring

### Check Logs

```bash
# All logs in one view
tail -f /var/log/unigames/*.log

# Individual services
tail -f /var/log/unigames/backend.log
tail -f /var/log/unigames/celery-worker.log
tail -f /var/log/unigames/celery-beat.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Service Management

```bash
# Restart all services
supervisorctl restart unigames:*

# Restart individual service
supervisorctl restart unigames:unigames-backend

# Stop all services
supervisorctl stop unigames:*

# Start all services
supervisorctl start unigames:*

# View status
supervisorctl status
```

### Database Access

```bash
# PostgreSQL
docker exec -it unigames-postgres psql -U scheduler_user -d scheduler_db

# Common queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM calendar_events;
SELECT COUNT(*) FROM email_tracking;
```

### Redis Monitoring

```bash
# Redis CLI
docker exec -it unigames-redis redis-cli

# Check queue length
LLEN celery

# Monitor commands
MONITOR
```

---

## ⚠️ Troubleshooting

### Backend won't start
```bash
# Check logs
tail -f /var/log/unigames/backend-error.log

# Common issues:
# - Database not ready: wait 30 seconds, restart
# - Missing .env variables: check .env file
# - Port already in use: check with `lsof -i :8000`
```

### Email agent not processing
```bash
# Check Celery worker
supervisorctl status unigames:unigames-celery-worker

# Check Celery beat
supervisorctl status unigames:unigames-celery-beat

# View logs
tail -f /var/log/unigames/celery-*.log

# Restart
supervisorctl restart unigames:unigames-celery-worker
supervisorctl restart unigames:unigames-celery-beat
```

### Database connection issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -c "SELECT 1;"

# Restart PostgreSQL
docker restart unigames-postgres
```

### Frontend not loading
```bash
# Check Nginx
systemctl status nginx
nginx -t

# Reload Nginx
systemctl reload nginx

# Check frontend build
ls -la /opt/unigames/frontend/dist

# Rebuild if needed
cd /opt/unigames/frontend
npm run build
systemctl reload nginx
```

---

## ✅ Deployment Success Criteria

- [ ] Application accessible at http://95.179.179.94
- [ ] Users can sign up and log in
- [ ] Google OAuth authentication works
- [ ] Voice recording and transcription works
- [ ] Tasks are created and scheduled
- [ ] Calendar events are created in Google Calendar
- [ ] Email agent processes emails every 60 seconds
- [ ] No errors in logs
- [ ] All 3 services running (backend, celery worker, celery beat)
- [ ] Database has proper schema
- [ ] Supervisor manages all processes
- [ ] Nginx serves frontend and proxies API

---

## 📞 Support

If issues occur during deployment:

1. **Check logs first**: `/var/log/unigames/*.log`
2. **Verify services**: `supervisorctl status`
3. **Check Docker**: `docker ps`
4. **Test database**: PostgreSQL and Redis connectivity
5. **Review environment**: `.env` file has correct values

**Common fixes:**
- Restart services: `supervisorctl restart unigames:*`
- Restart Docker: `docker-compose restart`
- Rebuild frontend: `cd frontend && npm run build`
- Check Nginx config: `nginx -t`

---

**Last Updated**: November 2025
**For**: Hackathon Submission - UniGames Intelligent Scheduler
