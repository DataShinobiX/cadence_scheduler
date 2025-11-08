#!/usr/bin/env python3
"""
Quick test script for the transcribe endpoint
Usage: python test_transcribe.py <audio_file_path>
"""

import sys
import requests
from pathlib import Path


def test_transcribe(audio_file_path: str, backend_url: str = "http://localhost:8000"):
    """Test the transcribe endpoint"""

    audio_path = Path(audio_file_path)

    # Check if file exists
    if not audio_path.exists():
        print(f"❌ Error: File '{audio_file_path}' not found!")
        return

    print(f"📁 Testing with file: {audio_path.name}")
    print(f"🔗 Backend URL: {backend_url}")
    print(f"📊 File size: {audio_path.stat().st_size / 1024:.2f} KB")
    print()

    # Send request
    print("📤 Sending request to /api/transcribe...")

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/webm")}
            response = requests.post(
                f"{backend_url}/api/transcribe",
                files=files,
                timeout=30
            )

        # Check response
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print()
            print("📝 Transcription:")
            print("-" * 60)
            print(result.get("transcript", "No transcript found"))
            print("-" * 60)
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend!")
        print("   Make sure the backend is running on http://localhost:8000")
        print("   Run: ./run_backend.sh")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main function"""

    if len(sys.argv) < 2:
        print("Usage: python test_transcribe.py <audio_file_path>")
        print()
        print("Example:")
        print("  python test_transcribe.py recording.webm")
        print("  python test_transcribe.py /path/to/audio.mp3")
        sys.exit(1)

    audio_file = sys.argv[1]
    test_transcribe(audio_file)


if __name__ == "__main__":
    main()
