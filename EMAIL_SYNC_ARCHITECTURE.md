# Email Sync Architecture - Per-User On-Demand

## Overview

The email sync system now operates **per-user on-demand** instead of scanning all users periodically. This is more efficient, privacy-focused, and scales better.

## How It Works

### Before (Old Approach - REMOVED)
```
❌ Celery Beat runs every 60 seconds
❌ Scans ALL users in database
❌ Checks emails for everyone, even if they're not online
❌ Privacy concern: constantly reading all users' emails
❌ Resource waste: checking emails for inactive users
```

### After (New Approach - IMPLEMENTED)
```
✅ Users trigger their own email sync
✅ Each user gets their own background task
✅ Only checks emails when user requests it
✅ Privacy-friendly: user-initiated
✅ Resource-efficient: on-demand only
```

## Architecture

### 1. API Endpoint: `/api/email/sync`

**File**: `app/api/email_sync.py`

**Usage**:
```bash
# User must be authenticated (session token in header)
POST /api/email/sync
Authorization: Bearer <session_token>
```

**Response**:
```json
{
  "status": "success",
  "message": "Email sync started",
  "task_id": "abc123-task-id",
  "user_id": "user-uuid"
}
```

**What it does**:
1. Gets current user from session token
2. Queues a Celery background task for that specific user
3. Returns task_id so user can check status

### 2. Background Task (Celery)

**File**: `app/tasks/email_checker.py`

**Task**: `check_emails_and_schedule(user_id: str)`

**What it does**:
1. Takes a specific `user_id` as parameter
2. Fetches that user's Gmail token from database
3. Uses `GoogleTokenManager` to get Gmail service (auto-refresh tokens)
4. Reads last 3 emails from that user's Gmail
5. Extracts actionable tasks using LLM
6. Saves tasks to database (linked to that user)
7. Schedules tasks in that user's Google Calendar

**Key code**:
```python
@app.task(name='app.tasks.email_checker.check_emails_and_schedule')
def check_emails_and_schedule(user_id: str):
    """
    Check emails for a SPECIFIC user (not all users).
    """
    # Get user's Gmail token from database
    # Use GoogleTokenManager for automatic token refresh
    # Read their emails
    # Create tasks for them
    # Schedule in their calendar
```

### 3. When Email Sync is Triggered

There are multiple ways to trigger email sync for a user:

#### Option A: Manual "Sync Emails" Button (Frontend)
```javascript
// Add this button to dashboard
async function syncEmails() {
  const response = await fetch('/api/email/sync', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('session_token')}`
    }
  });

  const data = await response.json();
  console.log('Email sync started:', data.task_id);
}
```

#### Option B: Auto-Sync on Login (Backend)
Modify `app/api/auth.py` login endpoint:
```python
@router.post("/api/auth/login")
async def login(email: str):
    # ... existing login logic ...

    # Trigger email sync for this user
    from app.tasks.email_checker import check_emails_and_schedule
    check_emails_and_schedule.delay(str(user_id))

    return {"session_token": token, "user": user_data}
```

#### Option C: Periodic Per-User (Optional)
If you want periodic checking for active users only:
```python
# In celery_app.py beat_schedule
app.conf.beat_schedule = {
    'sync-demo-user-emails': {
        'task': 'app.tasks.email_checker.check_emails_and_schedule',
        'schedule': 300.0,  # Every 5 minutes
        'args': ['e3eb56fd-dc18-4295-a5c5-39fbc25ae219'],  # Demo user ID
    }
}
```

## Benefits

### 1. Privacy
- Users control when their emails are checked
- No background scanning of all users' emails
- Transparent: user knows when sync happens

### 2. Performance
- Only processes emails for users who need it
- No wasted resources on inactive users
- Scales better as user count grows

### 3. Multi-User Ready
- Each user gets isolated email checking
- Uses their own Gmail tokens
- Tasks saved to their account only

### 4. Demo-Friendly
- For hackathon: trigger sync when demo user logs in
- For production: users click "Sync Emails" when they want

## Demo Setup

For your hackathon demo with `paritoshsingh1612@gmail.com`:

### Method 1: Auto-sync on Dashboard Load (Recommended)

**File**: `frontend/src/pages/Dashboard.jsx`

```jsx
useEffect(() => {
  // Auto-sync emails when dashboard loads
  const syncEmails = async () => {
    try {
      const response = await fetch(`${API_URL}/api/email/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('session_token')}`
        }
      });

      if (response.ok) {
        console.log('✅ Email sync started in background');
      }
    } catch (error) {
      console.error('Email sync error:', error);
    }
  };

  syncEmails();
}, []); // Run once on mount
```

### Method 2: Add "Sync Emails" Button

```jsx
<button
  onClick={async () => {
    const response = await fetch(`${API_URL}/api/email/sync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('session_token')}`
      }
    });
    const data = await response.json();
    alert('Email sync started! ' + data.message);
  }}
  className="btn-primary"
>
  📧 Sync Emails
</button>
```

### Method 3: Periodic for Demo User Only

**File**: `app/celery_app.py`

```python
app.conf.beat_schedule = {
    'sync-demo-user-emails': {
        'task': 'app.tasks.email_checker.check_emails_and_schedule',
        'schedule': 300.0,  # Every 5 minutes
        'args': [os.getenv('DEMO_USER_ID', 'e3eb56fd-dc18-4295-a5c5-39fbc25ae219')],
    }
}
```

Add to `.env`:
```bash
DEMO_USER_ID=e3eb56fd-dc18-4295-a5c5-39fbc25ae219
```

## Migration from Old System

### What Changed

1. **Celery Task Signature**:
   ```python
   # BEFORE
   check_emails_and_schedule()  # No parameters, checked all users

   # AFTER
   check_emails_and_schedule(user_id: str)  # Requires user_id
   ```

2. **Celery Beat Schedule**:
   ```python
   # BEFORE
   app.conf.beat_schedule = {
       'check-emails-every-minute': {
           'task': 'app.tasks.email_checker.check_emails_and_schedule',
           'schedule': 60.0
       }
   }

   # AFTER
   app.conf.beat_schedule = {}  # Empty - on-demand only
   ```

3. **API Endpoint Added**:
   - New: `POST /api/email/sync` - Trigger sync for current user
   - New: `GET /api/email/sync/status/{task_id}` - Check sync status

### Testing

```bash
# Start backend
source venv/bin/activate
python -m uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info --pool=solo

# Test API (with valid session token)
curl -X POST http://localhost:8000/api/email/sync \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Summary

**Old**: Periodic background task scans all users every 60 seconds
**New**: On-demand per-user email sync triggered by API call

**Result**:
- ✅ Better privacy (user-initiated)
- ✅ Better performance (only when needed)
- ✅ Multi-user ready (isolated per user)
- ✅ Demo-friendly (auto-trigger on login or button click)

---

**Created**: November 2025
**UniGames Intelligent Scheduler**
