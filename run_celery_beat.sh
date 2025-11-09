#!/bin/bash

###############################################################################
# Celery Beat Startup Script
# Runs the periodic task scheduler (checks emails every 5 minutes)
###############################################################################

set -e

echo "=========================================="
echo "Starting Celery Beat Scheduler"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Redis is running
if ! docker ps | grep -q scheduler_redis; then
    echo -e "${YELLOW}⚠️ Redis container not running. Starting Docker services...${NC}"
    docker-compose up -d
    sleep 3
fi

echo -e "${GREEN}✓ Redis is running${NC}"
echo ""

# Set environment variables (if not already set)
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-scheduler_db}
export DB_USER=${DB_USER:-scheduler_user}
export DB_PASSWORD=${DB_PASSWORD:-scheduler_pass}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

echo "Starting Celery Beat..."
echo ""
echo "Environment:"
echo "  - Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo "  - Redis: $REDIS_URL"
echo ""
echo "📧 Email checking will run every 5 minutes"
echo ""

# Run Celery beat
celery -A app.celery_app beat \
    --loglevel=info

# Note: Use Ctrl+C to stop the beat scheduler
