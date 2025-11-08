from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from openai import OpenAI
import uuid
from typing import Optional

from app.orchestration.state import create_initial_state

router = APIRouter()

# NOTE: API key and base URL are hard-coded per user request. Replace with env vars in production.
API_KEY = "sk-aU7KLAifP85EWxg4J7NFJg"
BASE_URL = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

@router.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Combined endpoint that:
    1. Transcribes audio (Step 2)
    2. Creates session and initializes AgentState (Step 3)

    This is the main entry point from the frontend voice recorder.
    """
    try:
        # Step 2: Transcribe the audio
        contents = await file.read()
        tmp_path = "temp_audio.webm"
        with open(tmp_path, "wb") as f:
            f.write(contents)

        with open(tmp_path, "rb") as f:
            # Request a plain text transcription
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        # The client returns a string when response_format="text"
        transcript_text = transcription if isinstance(transcription, str) else getattr(transcription, "text", str(transcription))

        print(f"✅ Transcription complete: {transcript_text[:100]}...")

        # Step 3: Create session and initialize AgentState
        session_id = str(uuid.uuid4())
        user_id = user_id or "default-user"  # Use provided user_id or default

        # Initialize AgentState
        state = create_initial_state(
            user_id=user_id,
            session_id=session_id,
            raw_transcript=transcript_text,
            user_preferences={}  # Can be expanded later
        )

        print(f"✅ Session created: {session_id}")
        print(f"   User: {user_id}")
        print(f"   Transcript: {transcript_text}")

        # Return both transcript and session info
        return {
            "transcript": transcript_text,
            "session_id": session_id,
            "user_id": user_id,
            "status": "session_initialized",
            "message": "Transcript created and session initialized. Ready for agent processing.",
            "state": dict(state)  # Include full state for debugging
        }

    except Exception as exc:
        print(f"❌ Error in transcribe endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
