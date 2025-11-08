#!/usr/bin/env python3
"""
Test the complete flow: Audio -> Transcription -> Session Creation -> AgentState
This demonstrates Steps 1-3 of the architecture
"""

import requests
import json
from pathlib import Path
import sys


def test_with_text(text: str):
    """
    Simulate the flow by sending text instead of audio
    (For quick testing without audio file)
    """

    backend_url = "http://localhost:8000"

    print("=" * 60)
    print("Testing Transcribe + Session Flow (Steps 2-3)")
    print("=" * 60)
    print()

    print("📝 Simulated Transcript:")
    print(f"   '{text}'")
    print()

    # Note: This is a simplified test. In reality:
    # 1. Frontend records audio
    # 2. Sends audio file to /api/transcribe
    # 3. Backend transcribes + creates session

    print("⚠️  Note: This test simulates the flow.")
    print("   In production, you would send an actual audio file.")
    print()
    print("   To test with real audio:")
    print("   curl -X POST 'http://localhost:8000/api/transcribe' \\")
    print("     -F 'file=@audio.webm' \\")
    print("     -F 'user_id=test-user-123'")
    print()


def test_with_audio(audio_file_path: str):
    """
    Test the complete flow with an actual audio file
    """

    backend_url = "http://localhost:8000"
    audio_path = Path(audio_file_path)

    if not audio_path.exists():
        print(f"❌ Error: Audio file not found: {audio_file_path}")
        return

    print("=" * 60)
    print("Testing Complete Flow: Audio → Transcript → Session")
    print("=" * 60)
    print()

    print(f"📁 Audio file: {audio_path.name}")
    print(f"📊 File size: {audio_path.stat().st_size / 1024:.2f} KB")
    print()

    print("🚀 Step 1: Sending audio to /api/transcribe...")
    print()

    try:
        with open(audio_path, "rb") as f:
            files = {
                "file": (audio_path.name, f, "audio/webm")
            }
            data = {
                "user_id": "test-user-123"
            }

            response = requests.post(
                f"{backend_url}/api/transcribe",
                files=files,
                data=data,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()

            print("✅ Success! Complete flow executed")
            print()
            print("=" * 60)
            print("STEP 2: Transcription")
            print("=" * 60)
            print(f"Transcript: {result['transcript']}")
            print()

            print("=" * 60)
            print("STEP 3: Session & AgentState Initialization")
            print("=" * 60)
            print(f"Status: {result['status']}")
            print(f"Session ID: {result['session_id']}")
            print(f"User ID: {result['user_id']}")
            print(f"Message: {result['message']}")
            print()

            print("🔍 AgentState Details:")
            print(f"   Created At: {result['state']['created_at']}")
            print(f"   Decomposed Tasks: {len(result['state']['decomposed_tasks'])} (empty, waiting for Agent 1)")
            print(f"   Scheduling Plan: {len(result['state']['scheduling_plan'])} (empty, waiting for Agent 2)")
            print(f"   Conflicts: {len(result['state']['conflicts'])} (empty)")
            print(f"   Needs User Input: {result['state']['needs_user_input']}")
            print()

            print("📦 Full AgentState:")
            print(json.dumps(result['state'], indent=2))
            print()
            print("=" * 60)
            print("✅ Steps 1-3 Complete!")
            print("=" * 60)
            print()
            print("Next Steps:")
            print("  - Agent 1 will decompose the transcript into tasks")
            print("  - Agent 2 will schedule the tasks")
            print("  - Agent 3 will add to Google Calendar")

        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend!")
        print("   Make sure backend is running: ./run_backend.sh")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with audio file
        test_with_audio(sys.argv[1])
    else:
        # Simulate with text
        text = "I need to meet Bob at 2 PM downtown, finish the pitch deck by EOD, and go to the gym after 5 PM"
        test_with_text(text)
        print()
        print("💡 To test with actual audio file:")
        print("   python test_schedule_flow.py your_audio.webm")
