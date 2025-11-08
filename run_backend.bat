@echo off
REM Run Backend Server Script for Windows
REM This script starts the FastAPI backend server

echo Starting Intelligent Scheduler Backend...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if .env exists
if not exist ".env" (
    echo .env file not found. Copying from .env.example...
    copy .env.example .env
    echo Please edit .env and add your API keys!
    echo.
)

echo Starting FastAPI server on http://localhost:8000
echo.
echo API Documentation available at:
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
