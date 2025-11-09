#!/bin/bash

###############################################################################
# System Health Check Script
# Verifies all components are working before deployment
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_check() {
    echo -n "$1... "
}

print_ok() {
    echo -e "${GREEN}✓ OK${NC}"
}

print_fail() {
    echo -e "${RED}✗ FAILED${NC}"
    echo -e "${RED}  $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo -e "${YELLOW}  $1${NC}"
}

ERRORS=0
WARNINGS=0

print_header "UniGames System Health Check"

# 1. Check .env file
print_header "1. Environment Configuration"

print_check "Checking .env file exists"
if [ -f ".env" ]; then
    print_ok
else
    print_fail ".env file not found! Copy from .env.example"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ".env" ]; then
    source .env

    print_check "Checking OPENAI_API_KEY"
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        print_fail "OPENAI_API_KEY not set or is placeholder"
        ERRORS=$((ERRORS + 1))
    else
        print_ok
    fi

    print_check "Checking GOOGLE_CLIENT_ID"
    if [ -z "$GOOGLE_CLIENT_ID" ] || [ "$GOOGLE_CLIENT_ID" = "your-client-id.apps.googleusercontent.com" ]; then
        print_fail "GOOGLE_CLIENT_ID not set or is placeholder"
        ERRORS=$((ERRORS + 1))
    else
        print_ok
    fi

    print_check "Checking GOOGLE_CLIENT_SECRET"
    if [ -z "$GOOGLE_CLIENT_SECRET" ] || [ "$GOOGLE_CLIENT_SECRET" = "your-client-secret" ]; then
        print_fail "GOOGLE_CLIENT_SECRET not set or is placeholder"
        ERRORS=$((ERRORS + 1))
    else
        print_ok
    fi

    print_check "Checking SECRET_KEY"
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "change-this-to-a-random-secret-key-in-production" ]; then
        print_warn "SECRET_KEY is default value. Generate secure key for production"
        WARNINGS=$((WARNINGS + 1))
    else
        print_ok
    fi
fi

# 2. Check Docker
print_header "2. Docker Services"

print_check "Checking Docker is installed"
if command -v docker &> /dev/null; then
    print_ok
else
    print_fail "Docker not installed"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking Docker is running"
if docker info &> /dev/null; then
    print_ok
else
    print_fail "Docker daemon not running. Start with: sudo systemctl start docker"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking docker-compose is installed"
if command -v docker-compose &> /dev/null; then
    print_ok
else
    print_fail "docker-compose not installed"
    ERRORS=$((ERRORS + 1))
fi

if docker info &> /dev/null; then
    print_check "Checking PostgreSQL container"
    if docker ps | grep -q unigames-postgres; then
        print_ok
    else
        print_warn "PostgreSQL container not running. Start with: docker-compose up -d"
        WARNINGS=$((WARNINGS + 1))
    fi

    print_check "Checking Redis container"
    if docker ps | grep -q unigames-redis; then
        print_ok
    else
        print_warn "Redis container not running. Start with: docker-compose up -d"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# 3. Check Python environment
print_header "3. Python Environment"

print_check "Checking Python 3 is installed"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ OK${NC} ($(python3 --version))"
else
    print_fail "Python 3 not installed"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking virtual environment"
if [ -d "venv" ]; then
    print_ok
else
    print_warn "Virtual environment not found. Create with: python3 -m venv venv"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate

    print_check "Checking FastAPI is installed"
    if python3 -c "import fastapi" 2>/dev/null; then
        print_ok
    else
        print_fail "FastAPI not installed. Run: pip install -r requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi

    print_check "Checking Celery is installed"
    if python3 -c "import celery" 2>/dev/null; then
        print_ok
    else
        print_fail "Celery not installed. Run: pip install -r requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi

    print_check "Checking OpenAI library is installed"
    if python3 -c "import openai" 2>/dev/null; then
        print_ok
    else
        print_fail "OpenAI library not installed. Run: pip install -r requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi

    print_check "Checking LangGraph is installed"
    if python3 -c "import langgraph" 2>/dev/null; then
        print_ok
    else
        print_fail "LangGraph not installed. Run: pip install -r requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 4. Check Node.js and Frontend
print_header "4. Frontend Environment"

print_check "Checking Node.js is installed"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ OK${NC} ($(node --version))"
else
    print_fail "Node.js not installed"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking npm is installed"
if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓ OK${NC} ($(npm --version))"
else
    print_fail "npm not installed"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "frontend" ]; then
    print_check "Checking frontend dependencies"
    if [ -d "frontend/node_modules" ]; then
        print_ok
    else
        print_warn "Frontend dependencies not installed. Run: cd frontend && npm install"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# 5. Check Database Connectivity
print_header "5. Database Connectivity"

if docker ps | grep -q unigames-postgres; then
    print_check "Checking PostgreSQL connection"
    if docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -c "SELECT 1" &> /dev/null; then
        print_ok
    else
        print_fail "Cannot connect to PostgreSQL. Check credentials in .env"
        ERRORS=$((ERRORS + 1))
    fi

    print_check "Checking database schema exists"
    TABLE_COUNT=$(docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    if [ "$TABLE_COUNT" -ge 5 ]; then
        echo -e "${GREEN}✓ OK${NC} ($TABLE_COUNT tables found)"
    else
        print_warn "Database schema incomplete. Run: ./setup_database.sh && ./setup_auth_db.sh"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

if docker ps | grep -q unigames-redis; then
    print_check "Checking Redis connection"
    if docker exec unigames-redis redis-cli ping &> /dev/null; then
        print_ok
    else
        print_fail "Cannot connect to Redis"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 6. Check Shell Scripts
print_header "6. Deployment Scripts"

for script in run_backend.sh run_celery_worker.sh run_celery_beat.sh start_email_agent.sh setup_database.sh setup_auth_db.sh deploy_to_vm.sh vm_setup_production.sh; do
    print_check "Checking $script"
    if [ -f "$script" ] && [ -x "$script" ]; then
        print_ok
    elif [ -f "$script" ]; then
        print_warn "Not executable. Run: chmod +x $script"
        WARNINGS=$((WARNINGS + 1))
    else
        print_fail "File not found: $script"
        ERRORS=$((ERRORS + 1))
    fi
done

# 7. Check File Structure
print_header "7. Application Structure"

print_check "Checking app directory"
if [ -d "app" ]; then
    print_ok
else
    print_fail "app/ directory not found"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking frontend directory"
if [ -d "frontend" ]; then
    print_ok
else
    print_fail "frontend/ directory not found"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking orchestration module"
if [ -d "app/orchestration" ]; then
    print_ok
else
    print_fail "app/orchestration/ directory not found"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking agents module"
if [ -d "app/agents" ]; then
    print_ok
else
    print_fail "app/agents/ directory not found"
    ERRORS=$((ERRORS + 1))
fi

# Summary
print_header "Health Check Summary"

echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "System is ready for deployment! 🚀"
    echo ""
    echo "Next steps:"
    echo "  1. Review PRE_DEPLOYMENT_CHECKLIST.md"
    echo "  2. Run: ./deploy_to_vm.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS WARNING(S)${NC}"
    echo ""
    echo "System is mostly ready, but please review warnings above."
    echo "You may proceed with deployment, but fix warnings for production."
    exit 0
else
    echo -e "${RED}✗ $ERRORS ERROR(S), $WARNINGS WARNING(S)${NC}"
    echo ""
    echo "Please fix the errors above before deployment."
    echo "Refer to PRE_DEPLOYMENT_CHECKLIST.md for help."
    exit 1
fi
