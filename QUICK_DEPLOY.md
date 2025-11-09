# 🚀 Quick Deployment Guide (5 Minutes)

## Prerequisites (Do This First!)

### 1. Get OpenAI API Key
- Visit: https://platform.openai.com/api-keys
- Create key with GPT-4 and Whisper access
- Copy the key (starts with `sk-...`)

### 2. Setup Google OAuth
- Visit: https://console.cloud.google.com/
- Create project → Enable APIs (Calendar + Gmail)
- Create OAuth 2.0 credentials
- **Add redirect URI**: `http://95.179.179.94:8000/api/v1/auth/callback`
- Copy Client ID and Client Secret

### 3. Update .env File

```bash
# Copy template
cp .env.production .env

# Edit with your keys
nano .env
```

Update these lines:
```bash
OPENAI_API_KEY=sk-YOUR_ACTUAL_KEY
GOOGLE_CLIENT_ID=YOUR_ACTUAL_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_ACTUAL_SECRET
SECRET_KEY=YOUR_RANDOM_SECRET  # Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save and exit (Ctrl+X, Y, Enter)

---

## Deploy (3 Commands)

### Command 1: Health Check
```bash
./check_system_health.sh
```
**Expected**: All checks should pass (or warnings only)

### Command 2: Deploy to VM
```bash
./deploy_to_vm.sh
```
**Expected**:
- SSH connection successful
- Files uploaded
- Dependencies installed
- "Deployment Complete!" message

### Command 3: Setup on VM
```bash
# SSH into VM
ssh root@95.179.179.94
# Password: K5v-n]r=n6RTK$Re

# Run setup
cd /opt/unigames
./vm_setup_production.sh
```

**Expected**:
```
========================================
Production Setup Complete!
========================================

Service URLs:
  - Frontend:  http://95.179.179.94
  - API:       http://95.179.179.94/api
```

---

## Verify (Open in Browser)

1. **Frontend**: http://95.179.179.94
   - Should see login page

2. **API Health**: http://95.179.179.94/api/health
   - Should return: `{"status": "healthy"}`

3. **API Docs**: http://95.179.179.94/api/docs
   - Should show interactive API docs

---

## Test Application

### 1. Create Account
- Click "Sign Up"
- Enter email and password
- Log in

### 2. Connect Google
- Click "Connect Google Calendar"
- Authorize access
- Should see success message

### 3. Voice Scheduling
- Click microphone icon
- Say: "Schedule a meeting tomorrow at 3pm"
- Should see task created and calendar event

### 4. Email Agent (Auto-runs every 60 seconds)
- Send email to your Gmail with task content
- Wait 1 minute
- Check tasks - should auto-create from email

---

## Check Services (On VM)

```bash
# All services status
supervisorctl status unigames:*

# View logs
tail -f /var/log/unigames/*.log

# Restart if needed
supervisorctl restart unigames:*
```

---

## Troubleshooting

### Services not running?
```bash
supervisorctl restart unigames:*
docker-compose restart
```

### Frontend not loading?
```bash
cd /opt/unigames/frontend
npm run build
systemctl reload nginx
```

### API errors?
```bash
tail -f /var/log/unigames/backend-error.log
```

---

## Complete Documentation

- **Full Guide**: `DEPLOYMENT_README.md`
- **Checklist**: `PRE_DEPLOYMENT_CHECKLIST.md`
- **Quick Reference**: `VM_DEPLOYMENT_QUICK_REFERENCE.md`
- **Technical Details**: `UNIGAMES_VM_DEPLOYMENT_GUIDE.md`

---

**VM Access**:
- Host: `95.179.179.94`
- User: `root`
- Password: `K5v-n]r=n6RTK$Re`
- SSH: `ssh root@95.179.179.94`

**Live Demo**: http://95.179.179.94

Good luck! 🎉
