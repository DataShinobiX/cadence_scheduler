# Complete Flow Guide - Integrated Agents

## 🎉 What's Working Now

You now have a complete end-to-end pipeline:

```
User Records Audio
    ↓
POST /api/transcribe
    ↓
┌─────────────────────────────────────────┐
│  STEP 2: Transcribe Audio              │
│  ✅ OpenAI Whisper API                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  STEP 3: Initialize Session             │
│  ✅ Create session_id                   │
│  ✅ Create AgentState                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  STEP 4: Agent 1 - Task Decomposer      │
│  ✅ Parse transcript with LLM           │
│  ✅ Extract tasks, priorities, times    │
│  ✅ Create travel tasks if needed       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  STEP 5: Agent 2 - Scheduler Brain      │
│  ✅ Fetch existing calendar from DB     │
│  ✅ Build availability matrix           │
│  ✅ Use LLM to find best time slots     │
│  ✅ Detect conflicts                    │
└─────────────────────────────────────────┘
    ↓
    Decision Point
    ↓          ↓
Conflicts?    No Conflicts
    ↓          ↓
┌──────┐    ┌─────────────────────────────┐
│ Ask  │    │ STEP 6: Agent 3 - Calendar  │
│ User │    │ (Placeholder for now)       │
└──────┘    └─────────────────────────────┘
    ↓
Return Results to Frontend
```

## 📁 New Files Created

1. **app/orchestration/agent_adapters.py**
   - `Agent1Adapter`: Connects TaskDecomposerLLM to AgentState
   - `Agent2Adapter`: Connects SchedulerBrain to AgentState
   - `Agent3Adapter`: Placeholder for calendar integration

2. **app/orchestration/scheduler_graph.py** (updated)
   - Uses LangGraph to orchestrate agents
   - Implements conditional logic for conflicts
   - Manages state flow between agents

3. **app/api/transcribe.py** (updated)
   - Now runs complete pipeline
   - Calls all agents automatically
   - Returns comprehensive results

## 🚀 How to Test

### 1. Start the Backend

```bash
./run_backend.sh
```

You should see:
```
Initializing scheduler graph...
--- ORCHESTRATOR: Compiling graph... ---
--- ORCHESTRATOR: Graph compiled successfully! ---
Scheduler graph ready!
```

### 2. Send Audio with cURL

```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@your_audio.webm" \
  -F "user_id=test-user-123"
```

### 3. Or Use the Frontend

Your frontend should work automatically! Just:
1. Record audio
2. Click submit
3. Wait for results

## 📤 Response Structure

### Success Response (No Conflicts)

```json
{
  "status": "success",
  "transcript": "I need to meet Bob at 2 PM and finish the pitch deck by EOD",
  "session_id": "abc-123-...",
  "user_id": "test-user-123",

  "decomposed_tasks": [
    {
      "kind": "travel",
      "title": "Travel to Bob's location",
      "duration_minutes": 30,
      "priority": "high",
      "priority_num": 1
    },
    {
      "kind": "activity",
      "title": "Meeting with Bob",
      "start": "2024-11-08T14:00:00",
      "duration_minutes": 60,
      "priority": "high",
      "priority_num": 1
    },
    {
      "kind": "activity",
      "title": "Finish pitch deck",
      "duration_minutes": 180,
      "priority": "high",
      "priority_num": 1,
      "constraints": ["before EOD"]
    }
  ],

  "scheduling_plan": [
    {
      "task_id": "uuid-1",
      "description": "Travel to Bob's location",
      "date": "2024-11-08",
      "start_time": "2024-11-08T13:30:00",
      "end_time": "2024-11-08T14:00:00",
      "duration_minutes": 30
    },
    {
      "task_id": "uuid-2",
      "description": "Meeting with Bob",
      "date": "2024-11-08",
      "start_time": "2024-11-08T14:00:00",
      "end_time": "2024-11-08T15:00:00",
      "duration_minutes": 60
    }
    // ...
  ],

  "conflicts": [],
  "needs_user_input": false,
  "message": "Successfully processed! Found 3 tasks and scheduled all 3 of them.",
  "errors": []
}
```

### Response with Conflicts

```json
{
  "status": "needs_input",
  "transcript": "...",
  "decomposed_tasks": [...],
  "scheduling_plan": [...],

  "conflicts": [
    {
      "task": "Finish pitch deck",
      "reason": "No available time slots found for the required duration of 180 minutes.",
      "suggestion": "Consider shortening the task, moving other events, or scheduling on another day."
    }
  ],

  "needs_user_input": true,
  "message": "Found 3 tasks. Successfully scheduled 2, but 1 tasks have conflicts that need your input."
}
```

## 🔍 What Happens in Backend Logs

When you send a request, you'll see:

```
============================================================
STEP 2: Transcribing audio...
============================================================
✅ Transcription complete: I need to meet Bob...

============================================================
STEP 3: Creating session and initializing AgentState...
============================================================
✅ Session created: abc-123-def-456
   User: test-user-123
   Transcript: I need to meet Bob at 2 PM...

============================================================
STEPS 4-6: Running Agent Orchestration...
============================================================

============================================================
ORCHESTRATOR: Calling Agent 1 (Task Decomposer)
============================================================

[AGENT 1] Task Decomposer starting...
[AGENT 1] Transcript: I need to meet Bob at 2 PM...
[AGENT 1] ✅ Decomposed 3 tasks
  1. Travel to Bob's location - Priority: high (1)
  2. Meeting with Bob - Priority: high (1)
  3. Finish pitch deck - Priority: high (1)

============================================================
ORCHESTRATOR: Calling Agent 2 (Scheduler Brain)
============================================================

[AGENT 2] Scheduler Brain starting...
[AGENT 2] Scheduling 3 tasks...
[AGENT 2] Using preferences: {'user_id': 'test-user-123', 'work_hours_start': '09:00', ...}

Asking LLM to choose best slot for: 'Travel to Bob's location'
LLM Reasoning: Selected slot_a as it provides a buffer before the meeting starts.

Asking LLM to choose best slot for: 'Meeting with Bob'
LLM Reasoning: This is the constraint time from the user, selecting slot at 14:00.

[AGENT 2] ✅ Scheduled 3 tasks
[AGENT 2] ⚠️ Found 0 conflicts
[AGENT 2] Scheduled tasks:
  - Travel to Bob's location at 2024-11-08T13:30:00
  - Meeting with Bob at 2024-11-08T14:00:00
  - Finish pitch deck at 2024-11-08T09:00:00

============================================================
ORCHESTRATOR: Calling Agent 3 (Calendar Integrator)
============================================================

[AGENT 3] Calendar Integrator starting...
[AGENT 3] ⚠️ Not yet implemented - using placeholder
[AGENT 3] ✅ Would create 3 calendar events

============================================================
✅ ORCHESTRATION COMPLETE
============================================================
```

## 🧪 Testing Options

### Option 1: Test Full Pipeline

```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.webm" \
  -F "user_id=test-user-123" \
  -F "run_agents=true"
```

### Option 2: Test Transcription Only (Skip Agents)

```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.webm" \
  -F "user_id=test-user-123" \
  -F "run_agents=false"
```

### Option 3: Use Swagger UI

1. Open http://localhost:8000/docs
2. Click on `POST /api/transcribe`
3. Click "Try it out"
4. Upload audio file
5. Set user_id (optional)
6. Set run_agents to `true`
7. Click "Execute"

## 📊 Data Flow Between Agents

### Agent 1 Output → Agent 2 Input

```python
# Agent 1 produces:
state["decomposed_tasks"] = [
    {
        "kind": "activity",
        "title": "Meeting with Bob",
        "duration_minutes": 60,
        "priority": "high",
        "priority_num": 1,
        "start": "2024-11-08T14:00:00",
        "constraints": ["at 14:00"]
    }
]

# Agent 2 receives this and uses:
tasks = state["decomposed_tasks"]
# Converts to internal Task objects
# Schedules them
# Returns:
state["scheduling_plan"] = [...]
state["conflicts"] = [...]
```

### Agent 2 Output → Agent 3 Input

```python
# Agent 2 produces:
state["scheduling_plan"] = [
    {
        "task_id": "uuid",
        "description": "Meeting with Bob",
        "date": "2024-11-08",
        "start_time": "2024-11-08T14:00:00",
        "end_time": "2024-11-08T15:00:00",
        "duration_minutes": 60,
        "location": "Office"
    }
]

# Agent 3 will use this to create Google Calendar events
```

## 🔧 Configuration

### Agent 1 (Task Decomposer)

Uses these environment variables:
- `OPENAI_API_KEY` (or hardcoded)
- `OPENAI_BASE_URL` (or hardcoded)
- `OPENAI_MODEL` (defaults to `gpt-4.1-mini`)

### Agent 2 (Scheduler Brain)

- Fetches calendar from database (requires user_id)
- Uses user preferences from state
- Default work hours: 09:00 - 18:00
- Default lunch: 13:00 (60 min)

### Agent 3 (Calendar Integrator)

Currently a placeholder - will integrate with Google Calendar API later.

## 🐛 Troubleshooting

### "No module named 'langchain_openai'"

```bash
pip install -r requirements.txt
```

### "Database connection failed"

Agent 2 tries to fetch calendar from database. Make sure:
```bash
docker-compose up -d db
```

Or it will use mock data.

### "LLM failed to choose slot"

Check that API keys are correct and the LLM endpoint is accessible.

### "Agents not running"

Check `run_agents` parameter is `true` (default).

## 📝 Next Steps

### Immediate
- ✅ Agent 1 integrated
- ✅ Agent 2 integrated
- ⏳ Agent 3 implementation (Google Calendar)

### Future
- Add conflict resolution UI in frontend
- Implement Agent 4 (Email Tracker)
- Implement Agent 5 (Weekly Recaps)
- Add session persistence
- Add real-time progress updates (WebSocket/SSE)

## 🎯 Key Features Working

1. ✅ **Intelligent Task Decomposition**
   - Understands complex requests
   - Creates travel tasks automatically
   - Extracts priorities and constraints

2. ✅ **Smart Scheduling**
   - Fetches existing calendar
   - Uses LLM for slot selection
   - Respects constraints ("after 5pm", "by EOD")
   - Considers work hours and lunch

3. ✅ **Conflict Detection**
   - Identifies scheduling conflicts
   - Provides alternatives
   - Flags when user input needed

4. ✅ **Complete Pipeline**
   - Audio → Transcript → Tasks → Schedule
   - One API call does everything
   - Comprehensive response

## 💡 Testing Tips

### Create Test Audio

**Simple text-to-speech:**
```bash
# Mac
say "I need to meet Bob at 2 PM downtown, finish the pitch deck by end of day, and go to the gym after 5 PM" -o test.aiff

# Convert to webm if needed
ffmpeg -i test.aiff test.webm
```

### Test Different Scenarios

1. **Simple scheduling:**
   ```
   "Schedule a meeting with Bob at 2 PM tomorrow"
   ```

2. **With conflicts:**
   ```
   "I have 5 meetings today from 9 AM to 5 PM, and I need to finish a 3-hour project by EOD"
   ```

3. **With constraints:**
   ```
   "Gym after 5 PM, lunch at 1 PM, and a call with Sarah sometime this week"
   ```

## 🎉 Success!

You now have:
- ✅ Complete transcription pipeline
- ✅ Two intelligent agents working together
- ✅ LangGraph orchestration
- ✅ Conflict detection
- ✅ Comprehensive API responses

Your intelligent scheduler is working end-to-end! 🚀
