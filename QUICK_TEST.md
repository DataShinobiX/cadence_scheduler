# Quick Test Guide

## 🚀 Start Backend

```bash
./run_backend.sh
```

Expected output:
```
Initializing scheduler graph...
--- ORCHESTRATOR: Compiling graph... ---
--- ORCHESTRATOR: Graph compiled successfully! ---
Scheduler graph ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🧪 Test 1: Without Audio (Fastest)

```bash
python test_complete_flow.py
```

This tests Agent 1 → Agent 2 with a sample transcript.

## 🎤 Test 2: With Audio (Full Pipeline)

```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@your_audio.webm" \
  -F "user_id=test-user-123"
```

## 🌐 Test 3: Using Browser

1. Open: http://localhost:8000/docs
2. Click: `POST /api/transcribe`
3. Click: "Try it out"
4. Upload audio file
5. Click: "Execute"

## 📊 Expected Response

```json
{
  "status": "success",
  "transcript": "I need to meet Bob at 2 PM...",
  "decomposed_tasks": [
    {
      "title": "Meeting with Bob",
      "priority": "high",
      "priority_num": 1
    }
  ],
  "scheduling_plan": [
    {
      "description": "Meeting with Bob",
      "start_time": "2024-11-08T14:00:00",
      "duration_minutes": 60
    }
  ],
  "conflicts": [],
  "needs_user_input": false,
  "message": "Successfully processed! Found 3 tasks and scheduled all 3 of them."
}
```

## ✅ What to Check

1. **Transcription works**: Check `transcript` field
2. **Agent 1 works**: Check `decomposed_tasks` has tasks
3. **Agent 2 works**: Check `scheduling_plan` has scheduled times
4. **No errors**: Check `errors` array is empty

## 🐛 If Something Fails

### Database Not Running
```bash
docker-compose up -d db
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Check Logs
Look for error messages in terminal where backend is running.

## 🎯 Sample Transcripts to Test

**Simple:**
```
"Schedule a meeting with Bob at 2 PM tomorrow"
```

**Complex:**
```
"I need to meet Bob at 2 PM downtown, finish the pitch deck by EOD, and go to the gym after 5 PM"
```

**With Constraints:**
```
"Gym after 6 PM, lunch at noon, and finish the report before 3 PM"
```

## 📝 Frontend Integration

Your frontend just needs to:

```javascript
const formData = new FormData();
formData.append('file', audioBlob, 'recording.webm');
formData.append('user_id', 'user-123');

const response = await fetch('http://localhost:8000/api/transcribe', {
  method: 'POST',
  body: formData
});

const result = await response.json();

// Display results
console.log('Transcript:', result.transcript);
console.log('Tasks:', result.decomposed_tasks);
console.log('Schedule:', result.scheduling_plan);
```

## ✨ That's It!

Your intelligent scheduler is ready to use! 🎉
