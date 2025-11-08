@echo off
REM Intelligent Scheduler - Database Setup Script for Windows
REM This script sets up the entire database environment for local development

setlocal enabledelayedexpansion

echo ======================================
echo Intelligent Scheduler - Database Setup
echo ======================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo [OK] Docker is installed
echo.

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose is not available!
        echo Please install Docker Compose or update Docker Desktop
        exit /b 1
    )
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo [OK] Docker Compose is available
echo.

REM Stop and remove existing containers
echo Cleaning up existing containers...
%DOCKER_COMPOSE_CMD% down -v 2>nul
echo.

REM Pull the latest images
echo Pulling latest Docker images...
%DOCKER_COMPOSE_CMD% pull
echo.

REM Start the database services
echo Starting database services...
%DOCKER_COMPOSE_CMD% up -d db redis
echo.

REM Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to be ready...
set MAX_RETRIES=30
set RETRY_COUNT=0

:wait_postgres
docker exec scheduler_db pg_isready -U scheduler_user -d scheduler_db >nul 2>&1
if errorlevel 1 (
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! geq %MAX_RETRIES% (
        echo [ERROR] PostgreSQL failed to start after %MAX_RETRIES% attempts
        %DOCKER_COMPOSE_CMD% logs db
        exit /b 1
    )
    echo Waiting... (!RETRY_COUNT!/%MAX_RETRIES%)
    timeout /t 2 /nobreak >nul
    goto wait_postgres
)

echo [OK] PostgreSQL is ready!
echo.

REM Wait for Redis to be ready
echo Waiting for Redis to be ready...
set RETRY_COUNT=0

:wait_redis
docker exec scheduler_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! geq %MAX_RETRIES% (
        echo [ERROR] Redis failed to start after %MAX_RETRIES% attempts
        %DOCKER_COMPOSE_CMD% logs redis
        exit /b 1
    )
    echo Waiting... (!RETRY_COUNT!/%MAX_RETRIES%)
    timeout /t 1 /nobreak >nul
    goto wait_redis
)

echo [OK] Redis is ready!
echo.

REM Verify database schema
echo Verifying database schema...
for /f %%i in ('docker exec scheduler_db psql -U scheduler_user -d scheduler_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"') do set TABLE_COUNT=%%i

if "%TABLE_COUNT%"=="0" (
    echo [ERROR] Database tables were not created!
    echo Checking logs...
    %DOCKER_COMPOSE_CMD% logs db
    exit /b 1
)

echo [OK] Database schema verified (%TABLE_COUNT% tables created)
echo.

REM Ask about pgAdmin
set /p PGADMIN="Do you want to start pgAdmin (Web UI for database management)? [y/N] "
if /i "%PGADMIN%"=="y" (
    echo Starting pgAdmin...
    %DOCKER_COMPOSE_CMD% up -d pgadmin
    echo [OK] pgAdmin is starting...
    echo    Access it at: http://localhost:5050
    echo    Email: admin@scheduler.com
    echo    Password: admin
    echo.
    echo    To add the database server in pgAdmin:
    echo    - Host: host.docker.internal
    echo    - Port: 5432
    echo    - Database: scheduler_db
    echo    - Username: scheduler_user
    echo    - Password: scheduler_pass
)
echo.

REM Display connection information
echo ======================================
echo [OK] Database Setup Complete!
echo ======================================
echo.
echo Connection Details:
echo   PostgreSQL:
echo     Host: localhost
echo     Port: 5432
echo     Database: scheduler_db
echo     Username: scheduler_user
echo     Password: scheduler_pass
echo.
echo   Redis:
echo     Host: localhost
echo     Port: 6379
echo.
echo   Connection String:
echo     postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db
echo.
echo Useful Commands:
echo   Stop all services:    docker-compose down
echo   View logs:            docker-compose logs -f
echo   Restart services:     docker-compose restart
echo   Remove all data:      docker-compose down -v
echo.
echo Next Steps:
echo   1. Copy .env.example to .env
echo   2. Update .env with your API keys
echo   3. Install Python dependencies: pip install -r requirements.txt
echo   4. Run the application: uvicorn app.main:app --reload
echo.
echo Happy coding!
echo.

pause
