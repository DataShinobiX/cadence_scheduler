from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request
from openai import OpenAI
import uuid
import os
from typing import Optional

from app.orchestration.state import create_initial_state
from app.orchestration.orchestrator import run_orchestration
from app.middleware.auth import require_auth

router = APIRouter()

# NOTE: API key and base URL are hard-coded per user request. Replace with env vars in production.
API_KEY = "sk-aU7KLAifP85EWxg4J7NFJg"
BASE_URL = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


@router.post("/api/transcribe")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    run_agents: Optional[str] = Form("true")  # Option to skip agents for testing
):
    """
    Complete pipeline:
    1. Authenticates user (required)
    2. Transcribes audio (Step 2)
    3. Creates session and initializes AgentState (Step 3)
    4. Runs agent orchestration (Steps 4-6): Agent 1 → Agent 2 → Agent 3
    5. Returns scheduling results

    This is the main entry point from the frontend voice recorder.

    Authentication required: Send session token in Authorization header.
    """
    try:
        # ====================================================================
        # STEP 1: Authenticate user
        # ====================================================================
        print("\n" + "=" * 60)
        print("STEP 1: Authenticating user...")
        print("=" * 60)

        user_id = require_auth(request)
        print(f"✅ Authenticated user: {user_id}")

        # ====================================================================
        # STEP 2: Transcribe the audio
        # ====================================================================
        print("\n" + "=" * 60)
        print("STEP 2: Transcribing audio...")
        print("=" * 60)

        contents = await file.read()
        tmp_path = "temp_audio.webm"
        with open(tmp_path, "wb") as f:
            f.write(contents)

        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        transcript_text = transcription if isinstance(transcription, str) else getattr(transcription, "text", str(transcription))

        print(f"✅ Transcription complete: {transcript_text[:100]}...")

        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        # ====================================================================
        # STEP 3: Create session and initialize AgentState
        # ====================================================================
        print("\n" + "=" * 60)
        print("STEP 3: Creating session and initializing AgentState...")
        print("=" * 60)

        session_id = str(uuid.uuid4())

        # Initialize AgentState (using authenticated user_id)
        state = create_initial_state(
            user_id=user_id,
            session_id=session_id,
            raw_transcript=transcript_text,
            user_preferences={}  # Can be expanded later
        )

        print(f"✅ Session created: {session_id}")
        print(f"   User: {user_id}")
        print(f"   Transcript: {transcript_text}")

        # ====================================================================
        # STEPS 4-6: Run Agent Orchestration
        # ====================================================================
        if run_agents.lower() == "true":
            print("\n" + "=" * 60)
            print("STEPS 4-6: Running Agent Orchestration...")
            print("=" * 60)

            try:
                # Delegate to the orchestrator
                final_state = run_orchestration(state)

                # Return comprehensive results
                return {
                    "status": "success" if not final_state.get("needs_user_input") else "needs_input",
                    "transcript": transcript_text,
                    "session_id": session_id,
                    "user_id": user_id,

                    # Agent outputs
                    "decomposed_tasks": final_state.get("decomposed_tasks", []),
                    "scheduling_plan": final_state.get("scheduling_plan", []),
                    "conflicts": final_state.get("conflicts", []),
                    "needs_user_input": final_state.get("needs_user_input", False),

                    # Metadata
                    "message": _generate_response_message(final_state),
                    "errors": final_state.get("errors", []),

                    # Full state (for debugging)
                    "state": dict(final_state)
                }

            except Exception as e:
                print(f"\n❌ Error during orchestration: {e}")
                import traceback
                traceback.print_exc()

                # Return partial results if orchestration failed
                return {
                    "status": "error",
                    "transcript": transcript_text,
                    "session_id": session_id,
                    "user_id": user_id,
                    "message": f"Transcription succeeded but orchestration failed: {str(e)}",
                    "errors": [str(e)],
                    "state": dict(state)
                }
        else:
            # Skip agents (for testing transcription only)
            return {
                "status": "session_initialized",
                "transcript": transcript_text,
                "session_id": session_id,
                "user_id": user_id,
                "message": "Transcript created and session initialized. Agents skipped.",
                "state": dict(state)
            }

    except Exception as exc:
        print(f"\n❌ Error in transcribe endpoint: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


def _generate_response_message(state: dict) -> str:
    """Generate a user-friendly message based on the final state"""

    num_tasks = len(state.get("decomposed_tasks", []))
    num_scheduled = len(state.get("scheduling_plan", []))
    num_conflicts = len(state.get("conflicts", []))

    if state.get("needs_user_input"):
        return (
            f"Found {num_tasks} tasks. Successfully scheduled {num_scheduled}, "
            f"but {num_conflicts} tasks have conflicts that need your input."
        )
    elif num_conflicts > 0:
        return (
            f"Found {num_tasks} tasks. Successfully scheduled {num_scheduled}. "
            f"{num_conflicts} tasks could not be scheduled."
        )
    else:
        return (
            f"Successfully processed! Found {num_tasks} tasks and scheduled all {num_scheduled} of them."
        )
