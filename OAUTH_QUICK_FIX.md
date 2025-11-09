# GOOGLE OAUTH - QUICK REFERENCE GUIDE

## Where 401 Errors Come From (Root Causes)

### 1. **Missing auth_sessions Table** (CRITICAL)
- **Location:** Database schema `/scripts/init_db.sql`
- **Impact:** Session authentication completely broken
- **Code references:** `/app/api/auth.py` lines 114, 186, 254
- **Fix:** Add CREATE TABLE statement (see OAUTH_ANALYSIS.md Section 9)

### 2. **Scheduler Uses File-Based Token Instead of Database**
- **Location:** `/app/orchestration/agent_adapters.py` line 247-250
- **Problem:** 
  - When `token.json` missing → tries OAuth flow
  - No browser available in background task → 401 error
  - Should use database token like frontend does
- **Current Code:**
  ```python
  integrator = SimplifiedCalendarIntegrator(
      credentials_file=self.credentials_file,
      token_file=self.token_file  # WRONG: Should be from DB
  )
  ```
- **Should Be:**
  ```python
  # Get token from database and refresh if needed
  # Similar to app/api/calendar.py _build_google_calendar_service()
  ```

### 3. **No Error Handling in Email Task**
- **Location:** `/app/tasks/email_checker.py` line 206-216
- **Problem:**
  - If token refresh fails → no error handling
  - Gmail API returns 401 → task silently fails
  - User doesn't know what happened
- **Missing:**
  ```python
  try:
      service = email_agent._build_gmail_service()
  except Exception as e:
      # Handle 401 error, notify user
  ```

### 4. **Token Expires Without Automatic Refresh**
- **Location:** Multiple places have outdated refresh logic
- **Scheduler Brain:** Uses file token (outdated method)
- **Email Task:** File token may expire between refreshes
- **Solution:** Use database tokens everywhere like `app/api/calendar.py` does

---

## Token Flow Comparison

### ✅ WORKING: Frontend Calendar API
```
GET /api/calendar/events
  ↓ require_auth(request) → get user_id
  ↓ _get_user_google_calendar_token(user_id)  [FROM DB]
  ↓ Credentials.from_authorized_user_info(token_json)
  ↓ if creds.expired: creds.refresh(Request())  [AUTO REFRESH]
  ↓ UPDATE database with new token  [PERSISTENCE]
  ↓ Return calendar events ✓
```

### ❌ BROKEN: Scheduler Brain
```
Agent 3 - Calendar Integrator
  ↓ SimplifiedCalendarIntegrator(token_file)  [FILE BASED]
  ↓ os.path.exists(self.token_file)  [CHECK FILE]
  ↓ If missing: InstalledAppFlow.run_local_server()  [NEEDS BROWSER!]
  ↓ Fails in background task
  ↓ 401 Error ✗
```

---

## Quick Fix Priority

### MUST DO (Next 1-2 hours):
1. Create `auth_sessions` table in database
2. Add error handling to email task (try-catch around service build)
3. Make scheduler use database token instead of file

### SHOULD DO (Next 1-2 days):
4. Move Gmail token to database (not just file)
5. Add proper token expiry monitoring
6. Test with expired tokens

### NICE TO HAVE:
7. Proactive token refresh queue
8. User notifications for reconnect needed
9. Multi-account support

---

## Key File Locations

| Problem | File | Lines | Issue |
|---------|------|-------|-------|
| Missing table | `/scripts/init_db.sql` | N/A | `auth_sessions` not created |
| Scheduler broken | `/app/orchestration/agent_adapters.py` | 247-250 | Uses file token |
| No error handling | `/app/tasks/email_checker.py` | 206-216 | No try-catch |
| Works well | `/app/api/calendar.py` | 74-127 | Good pattern to copy |
| File-based token | `/app/agents/email_tracking.py` | 51-65 | Should move to DB |

---

## Testing 401 Errors

### To Trigger 401 in Calendar API:
```bash
# Delete the google_calendar_token from database
UPDATE users SET google_calendar_token = NULL WHERE email = 'test@example.com';

# Call calendar API
GET /api/calendar/events

# Should return: 401 "Google Calendar not connected"
```

### To Trigger 401 in Email Task:
```bash
# Delete or corrupt token.json
rm token.json

# Run email check
celery -A app.celery_app call app.tasks.email_checker.check_emails_and_schedule

# Should fail with file not found or 401 error
```

### To Test Scheduler Brain:
```bash
# Delete token.json
rm app/models/token.json

# Create a task that triggers scheduling
# Should fail when trying to create calendar event

# Expected error: "Error building calendar service"
```

---

## Token Refresh Methods

### Method 1: Manual Refresh (Current)
```python
# User manually runs setup script
python setup_google_calendar.py user@example.com
# Browser opens, user clicks "Allow"
# Token saved to database
```

### Method 2: Automatic Refresh When Expired (PARTIAL)
```python
# In app/api/calendar.py - WORKS
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Update database
```

### Method 3: Background Task (NOT IMPLEMENTED)
```python
# What we need:
# Celery task runs daily
# Checks all user tokens
# Refreshes if expiring soon
# Avoids 401 errors

@app.task
def refresh_all_tokens():
    users = get_users_with_tokens()
    for user in users:
        if token_expires_soon(user.google_calendar_token):
            refresh_and_save_token(user)
```

---

## Database Token Format

```json
{
  "type": "authorized_user",
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "refresh_token": "1//LONG_REFRESH_TOKEN_HERE",
  "access_token": "ya29.LONG_ACCESS_TOKEN_HERE",
  "token_expiry": "2025-01-15T12:34:56Z",
  "scopes": [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
  ],
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id_issued_at": 1701234567,
  "token_expiry_datetime": "2025-01-15T12:34:56Z"
}
```

---

## Common Errors Decoded

### Error: "Google Calendar not connected"
**Cause:** `google_calendar_token` is NULL in database
**Fix:** Run `python setup_google_calendar.py`

### Error: "401 Unauthorized"
**Cause:** 
- Token expired and refresh_token missing
- Token file corrupted
- Refresh failed silently

**Fix:** 
1. Re-run setup script
2. Check error logs
3. Verify credentials.json exists

### Error: "No such file or directory: token.json"
**Cause:** Email task or scheduler looking for file that doesn't exist
**Fix:** 
1. Run `python generate_gmail_token.py`
2. Or change code to use database token

---

## Debugging Steps

### Check Database Token:
```sql
SELECT user_id, email, 
       CASE WHEN google_calendar_token IS NULL THEN 'MISSING' 
            ELSE 'EXISTS' END as calendar_token,
       CASE WHEN gmail_token IS NULL THEN 'MISSING' 
            ELSE 'EXISTS' END as gmail_token
FROM users;
```

### Check Token Validity:
```python
import json
from google.oauth2.credentials import Credentials

token_json = "SELECT google_calendar_token FROM users..."
token_data = json.loads(token_json)
creds = Credentials.from_authorized_user_info(token_data)

print(f"Valid: {creds.valid}")
print(f"Expired: {creds.expired}")
print(f"Has refresh token: {bool(creds.refresh_token)}")
print(f"Expiry: {creds.expiry}")
```

### Check File Tokens:
```bash
# Are token files where they should be?
ls -la token.json
ls -la app/models/token.json
ls -la app/agents/token.json

# Check if they're valid JSON
python -m json.tool token.json
```

---

## Success Indicators

✅ **Calendar API working:**
- GET /api/calendar/events returns events
- No 401 errors
- Token refreshes automatically when expired

✅ **Email task working:**
- Celery task runs every 5 minutes
- No "401 Unauthorized" in logs
- Tasks extracted from emails appear in database

✅ **Scheduler working:**
- Email tasks trigger calendar event creation
- Calendar events appear in Google Calendar
- No "401" or "token" errors in scheduler logs

---
