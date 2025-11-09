# 📘 Google OAuth for Judges - Complete Guide

## ✅ **YES, Judges Can Use Their Own Google Accounts!**

Your application is **fully multi-user** and supports any judge connecting their own Google Calendar and Gmail.

---

## 🎯 **How It Works for Judges**

### **Scenario**: Judge visits your hackathon demo

```
1. Judge opens: http://95.179.179.94
2. Judge signs up: judge@example.com
3. Judge clicks "Connect Google Calendar"
4. Google OAuth screen appears (Google's official login)
5. Judge logs in with THEIR Google account
6. Judge authorizes access to Calendar + Gmail
7. Tokens saved to YOUR database (linked to judge's account)
8. Judge can now:
   ✅ Schedule tasks via voice
   ✅ See THEIR calendar events
   ✅ Get tasks from THEIR Gmail
   ✅ All operations use THEIR Google data
```

---

## 🔐 **Complete User Flow**

### **Step 1: Sign Up / Log In**

**Judge visits**: http://95.179.179.94

**Frontend shows**:
- Sign Up form: Email + Name
- Or Log In form: Email only

**Judge enters**:
```
Email: judge.smith@gmail.com
Name: Judge Smith
```

**What happens**:
- New user created in YOUR database
- Session token generated
- Judge logged in
- Unique `user_id` assigned (UUID)

---

### **Step 2: Connect Google Account** (NEW!)

**Frontend shows**: "Connect Google Calendar" button

**Judge clicks button**

**Frontend makes request**:
```
GET http://95.179.179.94:8000/api/auth/google/connect?user_id=<judge-uuid>
```

**Backend redirects to Google**:
```
https://accounts.google.com/o/oauth2/auth?
    client_id=YOUR_CLIENT_ID&
    redirect_uri=http://95.179.179.94:8000/api/auth/google/callback&
    scope=https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.readonly&
    access_type=offline&
    prompt=consent
```

**Judge sees**: Google's official OAuth consent screen

```
┌─────────────────────────────────────────────────┐
│  Google Account                                  │
│                                                  │
│  Sign in with your Google Account               │
│  judge.smith@gmail.com                          │
│  [Enter password]                                │
│                                                  │
│  UniGames Scheduler wants to:                   │
│  ✓ See, edit, share, and delete calendars      │
│  ✓ Read your Gmail messages                     │
│                                                  │
│  [Cancel]  [Allow]                              │
└─────────────────────────────────────────────────┘
```

**Judge clicks "Allow"**

---

### **Step 3: OAuth Callback**

**Google redirects back to**:
```
http://95.179.179.94:8000/api/auth/google/callback?
    code=<authorization-code>&
    state=<judge-user-id>
```

**Backend**:
1. Receives authorization code
2. Exchanges code for tokens (access + refresh)
3. Saves tokens to database:
   ```sql
   UPDATE users
   SET google_calendar_token = '<judge-tokens>',
       gmail_token = '<judge-tokens>'
   WHERE user_id = '<judge-uuid>'
   ```
4. Redirects judge to:
   ```
   http://95.179.179.94/dashboard?success=google_connected
   ```

**Judge sees**: "✅ Google Calendar and Gmail connected!"

---

### **Step 4: Use the App with Judge's Data**

#### **Voice Scheduling**

**Judge records**: "Schedule a meeting with Bob tomorrow at 3pm"

**What happens**:
1. **Agent 1**: Transcribes audio
2. **Agent 2**: Extracts task: "Meeting with Bob, tomorrow 3pm"
3. **Agent 3**: Scheduler Brain
   - Loads **judge's calendar** (using judge's tokens)
   - Finds free slot
   - Schedules meeting
4. **Agent 4**: Calendar Integration
   - Uses `GoogleTokenManager(user_id=judge_uuid)`
   - Gets **judge's Calendar service** (automatic token refresh!)
   - Creates event in **judge's Google Calendar**

**Result**: Meeting appears in judge's actual Google Calendar! ✅

---

#### **Calendar Page**

**Judge clicks "Calendar" tab**

**Frontend requests**:
```
GET /api/calendar/events?user_id=<judge-uuid>&start_date=2025-11-09&end_date=2025-11-16
```

**Backend**:
1. Gets **judge's** `google_calendar_token` from database
2. Auto-refreshes if expired
3. Calls Google Calendar API with **judge's credentials**
4. Returns **judge's actual calendar events**

**Judge sees**: Their own calendar events! ✅

---

#### **Email Agent**

**Celery beat runs** (every 60 seconds)

**For judge's account**:
1. Gets **judge's** `gmail_token` from database
2. Auto-refreshes if expired
3. Connects to **judge's Gmail** account
4. Reads last 3 emails
5. Extracts tasks using LLM
6. Creates tasks in **judge's** task list
7. Schedules in **judge's** calendar

**Judge sees**: Tasks automatically created from their own emails! ✅

---

## 🔑 **Key Points**

### **1. Each Judge Gets Isolated Data**

```sql
users table:
┌─────────────┬──────────────────────┬─────────────────────┬────────────────────┐
│ user_id     │ email                │ google_calendar_... │ gmail_token        │
├─────────────┼──────────────────────┼─────────────────────┼────────────────────┤
│ uuid-111    │ judge1@gmail.com     │ {judge1-tokens}     │ {judge1-tokens}    │
│ uuid-222    │ judge2@gmail.com     │ {judge2-tokens}     │ {judge2-tokens}    │
│ uuid-333    │ judge3@gmail.com     │ {judge3-tokens}     │ {judge3-tokens}    │
└─────────────┴──────────────────────┴─────────────────────┴────────────────────┘
```

**Each judge's tokens are separate!**

---

### **2. All Operations Use Correct User's Data**

**Every API call includes `user_id`**:

```python
# Voice Scheduling
GoogleTokenManager(user_id=judge_uuid).get_calendar_service()
# → Uses JUDGE'S calendar tokens

# Calendar Page
_get_user_google_calendar_token(user_id=judge_uuid)
# → Returns JUDGE'S tokens

# Email Agent
_build_gmail_service(user_id=judge_uuid)
# → Uses JUDGE'S Gmail tokens
```

**Result**: Judge 1 sees Judge 1's data, Judge 2 sees Judge 2's data, etc. ✅

---

### **3. Automatic Token Refresh**

**Judge connects Google account once**:
- Access token valid for ~1 hour
- Refresh token valid forever

**After 1 hour**:
- Judge uses voice scheduling
- `GoogleTokenManager` checks if token expired
- Auto-refreshes using refresh token
- Saves new access token to database
- **Judge never knows this happened!**

**Judge never has to reconnect!** ✅

---

## 🎓 **What Judges Will See**

### **Dashboard After Connecting Google**

```
┌─────────────────────────────────────────────────────────────┐
│  UniGames Intelligent Scheduler                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👤 Welcome, Judge Smith (judge.smith@gmail.com)          │
│                                                             │
│  ✅ Google Calendar Connected                              │
│  ✅ Gmail Connected                                         │
│                                                             │
│  ┌────────────────────┐                                    │
│  │  🎤 Voice Command  │                                    │
│  │  Click to record   │                                    │
│  └────────────────────┘                                    │
│                                                             │
│  Recent Tasks:                                              │
│  ─────────────                                             │
│  • Meeting with Bob - Tomorrow 3pm ✅                       │
│  • Review submissions - Friday 10am ⏰                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### **Calendar View**

```
┌─────────────────────────────────────────────────────────────┐
│  📅 Your Calendar                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Monday, Nov 11                                             │
│  ─────────────────                                         │
│  09:00 - Team Standup (from your Gmail)                    │
│  11:00 - Code Review (scheduled via voice)                 │
│  14:00 - Meeting with Bob (scheduled via voice)            │
│                                                             │
│  Tuesday, Nov 12                                            │
│  ─────────────────                                         │
│  10:00 - Review submissions (from your Gmail)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**All events from judge's actual Google Calendar!**

---

## 🔐 **Security & Privacy**

### **Your Application**:
- ✅ Does NOT store judge's Google password
- ✅ Does NOT have access to other judges' data
- ✅ Uses industry-standard OAuth 2.0
- ✅ Tokens encrypted in transit (HTTPS in production)
- ✅ Each user isolated in database

### **Judge Can**:
- ✅ Revoke access anytime (in Google Account settings)
- ✅ See exactly what permissions app has
- ✅ Use their real Google account safely

### **What App Can Access**:
- ✅ Judge's Google Calendar (read + write)
- ✅ Judge's Gmail (read only)
- ❌ Cannot access judge's Google Drive
- ❌ Cannot access judge's Photos
- ❌ Cannot send emails on judge's behalf

---

## 📋 **Setup for Hackathon Demo**

### **Before Demo** (You do this):

1. **Update Google OAuth Redirect URI**:
   - Go to: https://console.cloud.google.com/
   - Find your OAuth credentials
   - Add redirect URI: `http://95.179.179.94:8000/api/auth/google/callback`
   - Save

2. **Update .env on VM**:
   ```bash
   GOOGLE_CLIENT_ID=your-actual-id
   GOOGLE_CLIENT_SECRET=your-actual-secret
   GOOGLE_REDIRECT_URI=http://95.179.179.94:8000/api/auth/google/callback
   FRONTEND_URL=http://95.179.179.94
   ```

3. **Deploy to VM**:
   ```bash
   ./deploy_to_vm.sh
   # Then on VM:
   cd /opt/unigames
   ./vm_setup_production.sh
   ```

---

### **During Demo** (Judges do this):

1. **Judge visits**: http://95.179.179.94
2. **Judge signs up**: Any email (e.g., `judge1@gmail.com`)
3. **Judge clicks**: "Connect Google Calendar"
4. **Judge logs in**: With their actual Google account
5. **Judge authorizes**: Allows Calendar + Gmail access
6. **Judge sees**: "✅ Connected!" message
7. **Judge tests**:
   - Voice command: "Schedule lunch tomorrow at noon"
   - Checks their Google Calendar → Event appears!
   - Checks Calendar tab → Shows their real events!

**Demo complete!** ✅

---

## 🎯 **Testing Before Demo**

### **Test with Your Own Account**:

```bash
# Start services
./run_backend.sh

# Open frontend
http://localhost:5173

# Sign up
Email: your-test@gmail.com
Name: Test User

# Click "Connect Google Calendar"
# → Redirects to Google
# → Log in with YOUR Google account
# → Click "Allow"
# → Redirected back to dashboard

# Test voice scheduling
"Schedule a test meeting in 2 hours"

# Check YOUR Google Calendar
# → Event should appear!
```

---

## ❓ **Common Questions**

### **Q: Can multiple judges use the app at the same time?**

**A**: Yes! Each judge has their own account and tokens. They can all use the app simultaneously without interfering with each other.

---

### **Q: Do judges need to use their work email or personal Gmail?**

**A**: They can use ANY email to sign up. Then they can connect ANY Google account (work or personal) for Calendar + Gmail integration.

Example:
- Sign up with: `judge@hackathon.com`
- Connect Google: `judge.personal@gmail.com` ✅

---

### **Q: What if a judge doesn't want to connect their Google account?**

**A**: They can still:
- ✅ Sign up and log in
- ✅ Use voice commands (tasks will be created)
- ❌ But tasks won't be added to Google Calendar (no token)
- ❌ Calendar page will show "Connect Google to see events"

---

### **Q: What happens after the hackathon? Do tokens stay?**

**A**: Tokens remain in database until:
- You delete the user
- Judge revokes access in Google settings
- Tokens auto-refresh forever otherwise

---

### **Q: Can we demo with fake/test data?**

**A**: Yes, two options:

**Option 1**: Create test Google account
- Create: `unigames-demo@gmail.com`
- Pre-populate calendar with test events
- Use this for demo

**Option 2**: Use judge's real account
- More impressive (shows real integration)
- Judge sees it work with their actual data

---

## 🎉 **Summary**

### **For You (Developer)**:
- ✅ Created complete Google OAuth flow
- ✅ Multi-user ready
- ✅ Automatic token refresh
- ✅ Production ready

### **For Judges**:
- ✅ Can use their own Google accounts
- ✅ Sees their own calendar data
- ✅ Gets tasks from their own Gmail
- ✅ All scheduled events go to their calendar
- ✅ Secure, isolated, private

### **For Demo**:
- ✅ Shows real Google integration
- ✅ Judges can test with real data
- ✅ Impressive and functional
- ✅ Enterprise-grade implementation

---

**Your app is ready for judges to use their own Google accounts!** 🚀

Each judge will have a completely isolated experience with their own calendar and email data. The multi-agent system will schedule tasks in their actual Google Calendar, and they'll see their real events in the app.

---

*Created: November 2025*
*UniGames Intelligent Scheduler - Multi-User Google OAuth Guide*
