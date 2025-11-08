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
