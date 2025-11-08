from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transcribe

app = FastAPI(title="Intelligent Scheduler API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transcribe.router)

@app.get("/")
async def root():
    return {
        "message": "Intelligent Scheduler API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "transcribe": "POST /api/transcribe - Transcribe audio and create session",
            "docs": "GET /docs - API documentation"
        }
    }



'''
<<<<<<< HEAD
import json
import os
from typing import Dict, Any

from app.agents.scheduler_brain import (
    schedule_tasks_for_next_seven_days,
    load_tasks_from_json,
)


def run_scheduler_brain_demo() -> Dict[str, Any]:
    """
    Small test entrypoint to exercise the scheduler brain API.
    """
    # Prepare preferences (user_id can be provided via env or defaults internally)
    user_preferences: Dict[str, Any] = {
        "user_id": os.getenv("TEST_USER_ID", "84d559ab-1792-4387-aa30-06982c0d5dcc"),
        "work_hours_start": "09:00",
        "work_hours_end": "18:00",
        "lunch_time_start": "13:00",
        "lunch_duration_minutes": 60,
        "most_productive_time": "morning",
    }

    # Load sample decomposed tasks from JSON
    tasks = load_tasks_from_json()

    # Call the new orchestrator-facing API
    result = schedule_tasks_for_next_seven_days(tasks, user_preferences)

    # Pretty print
    print("\n--- Scheduler Result ---")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run_scheduler_brain_demo()

'''