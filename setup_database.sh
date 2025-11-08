#!/bin/bash

# Intelligent Scheduler - Database Setup Script
# This script sets up the entire database environment for local development

set -e  # Exit on any error

echo "======================================"
echo "Intelligent Scheduler - Database Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available!${NC}"
    echo "Please install Docker Compose or update Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose is available${NC}"
echo ""

# Function to use docker compose (handles both docker-compose and docker compose)
docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

# Stop and remove existing containers (if any)
echo "🧹 Cleaning up existing containers..."
docker_compose_cmd down -v 2>/dev/null || true
echo ""

# Pull the latest images
echo "📥 Pulling latest Docker images..."
docker_compose_cmd pull
echo ""

# Start the database services
echo "🚀 Starting database services..."
docker_compose_cmd up -d db redis
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while ! docker exec scheduler_db pg_isready -U scheduler_user -d scheduler_db > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}❌ PostgreSQL failed to start after $MAX_RETRIES attempts${NC}"
        docker_compose_cmd logs db
        exit 1
    fi
    echo "Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
echo ""

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
RETRY_COUNT=0

while ! docker exec scheduler_redis redis-cli ping > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}❌ Redis failed to start after $MAX_RETRIES attempts${NC}"
        docker_compose_cmd logs redis
        exit 1
    fi
    echo "Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

echo -e "${GREEN}✅ Redis is ready!${NC}"
echo ""

# Verify database schema
echo "🔍 Verifying database schema..."
TABLE_COUNT=$(docker exec scheduler_db psql -U scheduler_user -d scheduler_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ Database tables were not created!${NC}"
    echo "Checking logs..."
    docker_compose_cmd logs db
    exit 1
fi

echo -e "${GREEN}✅ Database schema verified ($TABLE_COUNT tables created)${NC}"
echo ""

# Optional: Start pgAdmin
read -p "Do you want to start pgAdmin (Web UI for database management)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting pgAdmin..."
    docker_compose_cmd up -d pgadmin
    echo -e "${GREEN}✅ pgAdmin is starting...${NC}"
    echo "   Access it at: http://localhost:5050"
    echo "   Email: admin@scheduler.com"
    echo "   Password: admin"
    echo ""
    echo "   To add the database server in pgAdmin:"
    echo "   - Host: db (or host.docker.internal on Mac/Windows)"
    echo "   - Port: 5432"
    echo "   - Database: scheduler_db"
    echo "   - Username: scheduler_user"
    echo "   - Password: scheduler_pass"
fi
echo ""

# Display connection information
echo "======================================"
echo "✅ Database Setup Complete!"
echo "======================================"
echo ""
echo "📊 Connection Details:"
echo "   PostgreSQL:"
echo "     Host: localhost"
echo "     Port: 5432"
echo "     Database: scheduler_db"
echo "     Username: scheduler_user"
echo "     Password: scheduler_pass"
echo ""
echo "   Redis:"
echo "     Host: localhost"
echo "     Port: 6379"
echo ""
echo "   Connection String:"
echo "     postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
echo ""
echo "🔧 Useful Commands:"
echo "   Stop all services:    docker-compose down"
echo "   View logs:            docker-compose logs -f"
echo "   Restart services:     docker-compose restart"
echo "   Remove all data:      docker-compose down -v"
echo ""
echo "📝 Next Steps:"
echo "   1. Copy .env.example to .env"
echo "   2. Update .env with your API keys"
echo "   3. Install Python dependencies: pip install -r requirements.txt"
echo "   4. Run the application: uvicorn app.main:app --reload"
echo ""
echo "Happy coding! 🚀"
