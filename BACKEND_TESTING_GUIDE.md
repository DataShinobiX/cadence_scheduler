# Backend Testing Guide

This guide shows you how to run and test your FastAPI backend, specifically the transcribe functionality.

## Quick Start

### Option 1: Using the Run Script (Recommended)

**On Mac/Linux:**
```bash
./run_backend.sh
```

**On Windows:**
```bash
run_backend.bat
```

### Option 2: Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload --port 8000
```

## What Happens When Backend Starts

The server will start on: **http://localhost:8000**

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Available Endpoints

Once running, you have access to:

1. **Transcribe Endpoint**: `POST /api/transcribe`
2. **API Docs (Swagger)**: http://localhost:8000/docs
3. **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## Testing the Transcribe Endpoint

### Method 1: Using Swagger UI (Easiest)

1. Open http://localhost:8000/docs in your browser
2. Click on `POST /api/transcribe`
3. Click **"Try it out"**
4. Click **"Choose File"** and select an audio file (.webm, .mp3, .wav, etc.)
5. Click **"Execute"**
6. See the transcription result below!

### Method 2: Using cURL

```bash
# Test with an audio file
curl -X POST "http://localhost:8000/api/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/audio.webm"
```

Example response:
```json
{
  "transcript": "Hello, this is a test transcription of my audio file."
}
```

### Method 3: Using Python

```python
import requests

# Path to your audio file
audio_file_path = "test_audio.webm"

# Send request
with open(audio_file_path, "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/api/transcribe",
        files=files
    )

# Print result
print(response.json())
# Output: {'transcript': 'Your transcribed text here...'}
```

### Method 4: Using Your Frontend

If your frontend (on http://localhost:5173) is running:

1. Use the voice recorder in your frontend
2. Record some audio
3. Click submit/transcribe
4. The frontend will send the audio to your backend
5. Backend returns the transcription

## Testing with Sample Audio

### Create a Test Audio File

You can:
1. Record audio in your browser and save it
2. Use an online text-to-speech tool to generate audio
3. Use existing audio files (.webm, .mp3, .wav, .m4a)

### Quick Test Audio Generation

**Using macOS:**
```bash
# Generate test audio using macOS say command
say "This is a test of the transcription system" -o test_audio.aiff
```

**Using Python:**
```python
from gtts import gTTS

# Install: pip install gTTS
tts = gTTS("This is a test of the transcription system")
tts.save("test_audio.mp3")
```

## Monitoring Backend Logs

When you send a request to `/api/transcribe`, you'll see logs in your terminal:

```
INFO:     127.0.0.1:54321 - "POST /api/transcribe HTTP/1.1" 200 OK
```

If there's an error, you'll see detailed error messages.

## Common Issues & Solutions

### Issue: "ImportError: No module named 'fastapi'"

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Port 8000 is already in use"

**Solution:** Either:
- Kill the process using port 8000:
  ```bash
  # Find the process
  lsof -i :8000
  # Kill it
  kill -9 <PID>
  ```
- Or run on a different port:
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```

### Issue: "CORS error" when testing from frontend

**Solution:** Check that your frontend is running on http://localhost:5173. The CORS settings in `app/main.py` allow this origin.

If using a different port, update `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:YOUR_PORT"],  # Change this
    ...
)
```

### Issue: "OpenAI API error"

**Solution:** Your API key and endpoint are hardcoded in `app/api/transcribe.py`. Make sure they're valid:
```python
API_KEY = "sk-aU7KLAifP85EWxg4J7NFJg"
BASE_URL = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
```

## Advanced Testing

### Test with Different Audio Formats

The Whisper API supports:
- `.mp3`
- `.mp4`
- `.mpeg`
- `.mpga`
- `.m4a`
- `.wav`
- `.webm`

Try testing with different formats:
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3"

curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.wav"
```

### Test Error Handling

**Test with invalid file:**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@invalid.txt"
```

Should return an error response.

**Test with no file:**
```bash
curl -X POST "http://localhost:8000/api/transcribe"
```

Should return a 422 validation error.

## Debugging Tips

### Enable Debug Mode

In `app/main.py`, you can enable debug mode:
```python
app = FastAPI(debug=True)
```

### View Detailed Logs

Run with more verbose logging:
```bash
uvicorn app.main:app --reload --log-level debug
```

### Test with curl -v (Verbose)

```bash
curl -v -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.webm"
```

This shows request/response headers and other details.

## Performance Testing

### Test Response Time

```bash
time curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.webm"
```

### Test with Multiple Files

```bash
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/transcribe" \
    -F "file=@audio.webm"
done
```

## Integration with Frontend

Your backend is configured to accept requests from `http://localhost:5173` (Vite dev server).

**Frontend fetch example:**
```javascript
const formData = new FormData();
formData.append('file', audioBlob, 'recording.webm');

const response = await fetch('http://localhost:8000/api/transcribe', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data.transcript);
```

## Production Notes

Before deploying to production:

1. **Move API keys to environment variables:**
   ```python
   import os
   API_KEY = os.getenv("OPENAI_API_KEY")
   BASE_URL = os.getenv("OPENAI_BASE_URL")
   ```

2. **Update CORS settings:**
   ```python
   allow_origins=["https://your-production-domain.com"]
   ```

3. **Add rate limiting** to prevent abuse

4. **Add authentication** to protect your endpoints

5. **Use production ASGI server:**
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## Quick Reference

```bash
# Start backend
./run_backend.sh

# Test transcribe endpoint
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.webm"

# View API docs
open http://localhost:8000/docs

# Stop backend
Ctrl+C

# Run on different port
uvicorn app.main:app --reload --port 8001
```

## Next Steps

1. ✅ Backend is running
2. ✅ Transcribe endpoint is working
3. ⏳ Test from your frontend
4. ⏳ Add more endpoints (scheduling, agents, etc.)

---

Happy testing! 🚀
