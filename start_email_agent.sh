#!/bin/bash

###############################################################################
# Email Agent Startup Script
# Starts both Celery Worker and Beat in the background
###############################################################################

set -e

echo "=========================================="
echo "Starting Email Agent"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Redis is running
if ! docker ps | grep -q scheduler_redis; then
    echo -e "${YELLOW}⚠️ Redis not running. Starting Docker services...${NC}"
    docker-compose up -d
    sleep 3
fi

echo -e "${GREEN}✓ Redis is running${NC}"

# Set environment variables
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-scheduler_db}
export DB_USER=${DB_USER:-scheduler_user}
export DB_PASSWORD=${DB_PASSWORD:-scheduler_pass}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

echo ""
echo "Starting Celery Worker (background)..."

# Start worker in background with solo pool (fixes SIGSEGV with OpenAI/LangChain)
nohup celery -A app.celery_app worker \
    --loglevel=info \
    --pool=solo \
    > celery-worker.log 2>&1 &

WORKER_PID=$!
echo -e "${GREEN}✓ Celery Worker started (PID: $WORKER_PID)${NC}"
echo "  Logs: celery-worker.log"

sleep 2

echo ""
echo "Starting Celery Beat (background)..."

# Start beat in background
nohup celery -A app.celery_app beat \
    --loglevel=info \
    > celery-beat.log 2>&1 &

BEAT_PID=$!
echo -e "${GREEN}✓ Celery Beat started (PID: $BEAT_PID)${NC}"
echo "  Logs: celery-beat.log"

sleep 2

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Email Agent is Running!${NC}"
echo "=========================================="
echo ""
echo "📧 Emails will be checked every 5 minutes"
echo ""
echo "Monitor logs:"
echo "  Worker: tail -f celery-worker.log"
echo "  Beat:   tail -f celery-beat.log"
echo ""
echo "Process IDs:"
echo "  Worker: $WORKER_PID"
echo "  Beat:   $BEAT_PID"
echo ""
echo "To stop:"
echo "  kill $WORKER_PID $BEAT_PID"
echo "  or run: ./stop_email_agent.sh"
echo ""

# Save PIDs to file for easy stopping
echo "$WORKER_PID" > celery-worker.pid
echo "$BEAT_PID" > celery-beat.pid

echo "PIDs saved to celery-worker.pid and celery-beat.pid"
echo ""
