#!/bin/bash

###############################################################################
# Stop Email Agent
# Stops Celery Worker and Beat processes
###############################################################################

echo "=========================================="
echo "Stopping Email Agent"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Stop worker
if [ -f celery-worker.pid ]; then
    WORKER_PID=$(cat celery-worker.pid)
    if ps -p $WORKER_PID > /dev/null 2>&1; then
        echo "Stopping Celery Worker (PID: $WORKER_PID)..."
        kill $WORKER_PID
        echo -e "${GREEN}✓ Worker stopped${NC}"
    else
        echo "Worker already stopped"
    fi
    rm celery-worker.pid
else
    echo "No worker PID file found"
fi

# Stop beat
if [ -f celery-beat.pid ]; then
    BEAT_PID=$(cat celery-beat.pid)
    if ps -p $BEAT_PID > /dev/null 2>&1; then
        echo "Stopping Celery Beat (PID: $BEAT_PID)..."
        kill $BEAT_PID
        echo -e "${GREEN}✓ Beat stopped${NC}"
    else
        echo "Beat already stopped"
    fi
    rm celery-beat.pid
else
    echo "No beat PID file found"
fi

# Kill any remaining celery processes
echo ""
echo "Checking for remaining celery processes..."
CELERY_PIDS=$(ps aux | grep "[c]elery" | awk '{print $2}')

if [ -n "$CELERY_PIDS" ]; then
    echo "Found remaining processes, killing..."
    echo "$CELERY_PIDS" | xargs kill 2>/dev/null || true
    echo -e "${GREEN}✓ All celery processes stopped${NC}"
else
    echo "No remaining processes found"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Email Agent Stopped${NC}"
echo "=========================================="
echo ""
