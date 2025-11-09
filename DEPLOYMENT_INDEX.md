# 📚 UniGames Deployment Documentation Index

## 🎯 Start Here

**New to deployment?** → Read `QUICK_DEPLOY.md` (5 minutes)

**Need complete guide?** → Read `DEPLOYMENT_README.md` (15 minutes)

**Ready to deploy?** → Follow `PRE_DEPLOYMENT_CHECKLIST.md`

---

## 📖 Documentation Files

### 1. Quick Start Guides

| File | Purpose | Time to Read |
|------|---------|--------------|
| **QUICK_DEPLOY.md** | Fast 3-step deployment process | 5 min |
| **DEPLOYMENT_SUMMARY.md** | Complete deployment summary | 10 min |

### 2. Complete Guides

| File | Purpose | Pages |
|------|---------|-------|
| **DEPLOYMENT_README.md** | Full deployment documentation | Long |
| **PRE_DEPLOYMENT_CHECKLIST.md** | Step-by-step checklist | Long |
| **UNIGAMES_VM_DEPLOYMENT_GUIDE.md** | Technical architecture guide | Very Long |
| **VM_DEPLOYMENT_QUICK_REFERENCE.md** | Quick command reference | Medium |

### 3. Feature Documentation

| File | Purpose |
|------|---------|
| **SCHEDULER_CONFLICT_FIXES.md** | Conflict resolution system |
| **REMINDERS_TAB.md** | Notification history feature |

### 4. Scripts

| Script | Purpose | Run On |
|--------|---------|--------|
| `deploy_to_vm.sh` | Deploy application to VM | Local machine |
| `vm_setup_production.sh` | Setup production environment | VM |
| `check_system_health.sh` | Pre-deployment health check | Local machine |
| `verify_deployment.sh` | Post-deployment verification | VM |

---

## 🚀 Deployment Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

1. PREREQUISITES (5 min)
   ↓
   - Get OpenAI API key
   - Setup Google OAuth (Client ID + Secret)
   - Update .env file
   ↓
   READ: QUICK_DEPLOY.md or PRE_DEPLOYMENT_CHECKLIST.md

2. PRE-DEPLOYMENT CHECK (2 min)
   ↓
   RUN: ./check_system_health.sh
   ↓
   ✅ All checks pass → Continue
   ❌ Errors found → Fix and retry

3. DEPLOY TO VM (5 min)
   ↓
   RUN: ./deploy_to_vm.sh
   ↓
   - Uploads application to VM
   - Installs system dependencies
   ↓
   ✅ "Deployment Complete!" → Continue

4. SETUP PRODUCTION ON VM (10 min)
   ↓
   SSH: ssh root@95.179.179.94
   RUN: cd /opt/unigames && ./vm_setup_production.sh
   ↓
   - Installs Python dependencies
   - Creates database schema
   - Builds frontend
   - Configures Nginx
   - Starts all services
   ↓
   ✅ "Production Setup Complete!" → Continue

5. VERIFY DEPLOYMENT (2 min)
   ↓
   RUN: ./verify_deployment.sh
   ↓
   ✅ All checks pass → DONE! 🎉
   ❌ Issues found → Check logs, restart services

6. TEST APPLICATION
   ↓
   BROWSER: http://95.179.179.94
   ↓
   - Sign up / Log in
   - Connect Google account
   - Test voice scheduling
   - Test email agent
   ↓
   ✅ All features work → SUCCESS! 🚀
```

---

## 📋 What to Read When

### Before Deployment

1. **QUICK_DEPLOY.md** - Quick overview
2. **PRE_DEPLOYMENT_CHECKLIST.md** - Ensure you have everything
3. **DEPLOYMENT_SUMMARY.md** - Understand what gets deployed

### During Deployment

1. **QUICK_DEPLOY.md** - Follow 3-step process
2. **DEPLOYMENT_README.md** - Reference for detailed steps

### After Deployment

1. **VM_DEPLOYMENT_QUICK_REFERENCE.md** - Command reference
2. **DEPLOYMENT_README.md** - Troubleshooting section

### Understanding Features

1. **SCHEDULER_CONFLICT_FIXES.md** - How conflict resolution works
2. **REMINDERS_TAB.md** - Notification system
3. **UNIGAMES_VM_DEPLOYMENT_GUIDE.md** - Full architecture

---

## 🎯 Common Tasks

### I want to: Deploy the application

**Read**: QUICK_DEPLOY.md → PRE_DEPLOYMENT_CHECKLIST.md

**Run**:
```bash
# Local machine
./check_system_health.sh
./deploy_to_vm.sh

# On VM
ssh root@95.179.179.94
cd /opt/unigames
./vm_setup_production.sh
./verify_deployment.sh
```

### I want to: Understand the architecture

**Read**: UNIGAMES_VM_DEPLOYMENT_GUIDE.md → DEPLOYMENT_README.md

### I want to: Troubleshoot issues

**Read**: DEPLOYMENT_README.md (Troubleshooting section)

**Check**:
```bash
# On VM
supervisorctl status unigames:*
tail -f /var/log/unigames/*.log
docker ps
```

### I want to: Check service status

**Read**: VM_DEPLOYMENT_QUICK_REFERENCE.md

**Run**:
```bash
# On VM
supervisorctl status unigames:*
./verify_deployment.sh
curl http://localhost/api/health
```

### I want to: Restart services

**Read**: VM_DEPLOYMENT_QUICK_REFERENCE.md

**Run**:
```bash
# On VM
supervisorctl restart unigames:*
docker-compose restart
systemctl restart nginx
```

### I want to: View logs

**Read**: DEPLOYMENT_README.md (Monitoring section)

**Run**:
```bash
# On VM
tail -f /var/log/unigames/*.log
tail -f /var/log/unigames/backend.log
tail -f /var/log/unigames/celery-worker.log
```

### I want to: Access the database

**Read**: VM_DEPLOYMENT_QUICK_REFERENCE.md

**Run**:
```bash
# On VM
docker exec -it unigames-postgres psql -U scheduler_user -d scheduler_db
```

### I want to: Update environment variables

**Edit**:
```bash
# On VM
nano /opt/unigames/.env
supervisorctl restart unigames:*
```

### I want to: Rebuild frontend

**Run**:
```bash
# On VM
cd /opt/unigames/frontend
npm run build
systemctl reload nginx
```

---

## 🔍 Documentation Quick Reference

| Task | File | Section |
|------|------|---------|
| First-time deployment | QUICK_DEPLOY.md | All |
| Detailed deployment | DEPLOYMENT_README.md | Deployment Steps |
| Pre-deployment prep | PRE_DEPLOYMENT_CHECKLIST.md | Before Deployment |
| Environment setup | DEPLOYMENT_README.md | Prerequisites |
| Service management | VM_DEPLOYMENT_QUICK_REFERENCE.md | Service Management |
| Troubleshooting | DEPLOYMENT_README.md | Troubleshooting |
| Architecture overview | UNIGAMES_VM_DEPLOYMENT_GUIDE.md | Architecture |
| Database schema | UNIGAMES_VM_DEPLOYMENT_GUIDE.md | Database Section |
| API endpoints | DEPLOYMENT_README.md | Verification |
| Conflict resolution | SCHEDULER_CONFLICT_FIXES.md | All |
| Email agent | UNIGAMES_VM_DEPLOYMENT_GUIDE.md | Email Agent |
| Monitoring | DEPLOYMENT_README.md | Monitoring |

---

## 📊 File Sizes & Reading Times

| File | Size | Read Time |
|------|------|-----------|
| QUICK_DEPLOY.md | 2 KB | 5 min |
| DEPLOYMENT_SUMMARY.md | 15 KB | 10 min |
| DEPLOYMENT_README.md | 25 KB | 15 min |
| PRE_DEPLOYMENT_CHECKLIST.md | 12 KB | 10 min |
| VM_DEPLOYMENT_QUICK_REFERENCE.md | 10 KB | 8 min |
| UNIGAMES_VM_DEPLOYMENT_GUIDE.md | 29 KB | 20 min |
| SCHEDULER_CONFLICT_FIXES.md | 8 KB | 8 min |
| REMINDERS_TAB.md | 6 KB | 6 min |

**Total Documentation**: ~107 KB

---

## 🎓 Learning Path

### Beginner (Never deployed before)

1. Read: QUICK_DEPLOY.md
2. Read: PRE_DEPLOYMENT_CHECKLIST.md
3. Run: ./check_system_health.sh
4. Run: ./deploy_to_vm.sh
5. Follow: On-screen instructions

### Intermediate (Some deployment experience)

1. Read: DEPLOYMENT_SUMMARY.md
2. Skim: DEPLOYMENT_README.md
3. Run: ./deploy_to_vm.sh
4. Reference: VM_DEPLOYMENT_QUICK_REFERENCE.md as needed

### Advanced (Experienced DevOps)

1. Read: DEPLOYMENT_SUMMARY.md
2. Reference: UNIGAMES_VM_DEPLOYMENT_GUIDE.md for architecture
3. Run: ./deploy_to_vm.sh
4. Customize: Nginx, Supervisor configs as needed

---

## 🛠️ Scripts Overview

### Local Machine Scripts

**check_system_health.sh**
- Purpose: Verify local setup before deployment
- Checks: Environment variables, Docker, Python, Node.js
- Run: Before deployment
- Exit codes: 0 = success, 1 = errors

**deploy_to_vm.sh**
- Purpose: Deploy application to VM
- Actions: Upload files, install dependencies
- Run: After health check passes
- Output: SSH commands for next steps

### VM Scripts

**vm_setup_production.sh**
- Purpose: Complete production setup
- Actions: Install dependencies, configure services, start everything
- Run: Once after initial deployment
- Duration: ~10 minutes

**verify_deployment.sh**
- Purpose: Verify all services are working
- Checks: Services, ports, databases, endpoints
- Run: After production setup
- Exit codes: 0 = all checks pass, 1 = issues found

---

## 🎯 Success Checklist

After deployment, ensure:

- [ ] Read QUICK_DEPLOY.md or DEPLOYMENT_SUMMARY.md
- [ ] Obtained OpenAI API key
- [ ] Setup Google OAuth (Client ID + Secret)
- [ ] Updated .env file
- [ ] Ran ./check_system_health.sh (passed)
- [ ] Ran ./deploy_to_vm.sh (successful)
- [ ] SSH into VM successful
- [ ] Ran ./vm_setup_production.sh (completed)
- [ ] Ran ./verify_deployment.sh (all checks passed)
- [ ] Application accessible at http://95.179.179.94
- [ ] API health check responds
- [ ] Tested sign up/login
- [ ] Tested Google OAuth
- [ ] Tested voice scheduling
- [ ] Verified email agent running
- [ ] All services running in Supervisor
- [ ] No errors in logs

---

## 📞 Quick Help

**Can't connect to VM?**
→ Check SSH credentials in QUICK_DEPLOY.md

**Services not starting?**
→ See DEPLOYMENT_README.md → Troubleshooting

**Database errors?**
→ See DEPLOYMENT_README.md → Database Issues

**Frontend not loading?**
→ See DEPLOYMENT_README.md → Frontend Issues

**Need command reference?**
→ See VM_DEPLOYMENT_QUICK_REFERENCE.md

**Want to understand architecture?**
→ See UNIGAMES_VM_DEPLOYMENT_GUIDE.md

---

## 🎉 You're Ready!

All documentation is complete and organized.

**Start with**: QUICK_DEPLOY.md

**VM Access**:
- Host: 95.179.179.94
- User: root
- Password: K5v-n]r=n6RTK$Re

**After Deployment**:
- Frontend: http://95.179.179.94
- API: http://95.179.179.94/api
- API Docs: http://95.179.179.94/api/docs

Good luck with your hackathon! 🚀

---

**Last Updated**: November 2025
**Status**: ✅ Complete and Ready for Deployment
