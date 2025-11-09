#!/bin/bash

###############################################################################
# Deployment Verification Script (Run on VM after deployment)
# Checks if all services are working correctly
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

ERRORS=0

print_header "UniGames Deployment Verification"

# 1. Check Supervisor services
print_header "1. Supervisor Services"

print_check "Checking FastAPI backend"
if supervisorctl status unigames:unigames-backend | grep -q RUNNING; then
    print_ok
else
    print_fail "Backend not running. Check logs: tail -f /var/log/unigames/backend-error.log"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking Celery worker"
if supervisorctl status unigames:unigames-celery-worker | grep -q RUNNING; then
    print_ok
else
    print_fail "Celery worker not running. Check logs: tail -f /var/log/unigames/celery-worker-error.log"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking Celery beat"
if supervisorctl status unigames:unigames-celery-beat | grep -q RUNNING; then
    print_ok
else
    print_fail "Celery beat not running. Check logs: tail -f /var/log/unigames/celery-beat-error.log"
    ERRORS=$((ERRORS + 1))
fi

# 2. Check Docker containers
print_header "2. Docker Containers"

print_check "Checking PostgreSQL container"
if docker ps | grep -q unigames-postgres; then
    print_ok
else
    print_fail "PostgreSQL container not running. Run: docker-compose up -d"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking Redis container"
if docker ps | grep -q unigames-redis; then
    print_ok
else
    print_fail "Redis container not running. Run: docker-compose up -d"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check Nginx
print_header "3. Nginx Web Server"

print_check "Checking Nginx is running"
if systemctl is-active --quiet nginx; then
    print_ok
else
    print_fail "Nginx not running. Run: systemctl start nginx"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking Nginx configuration"
if nginx -t &> /dev/null; then
    print_ok
else
    print_fail "Nginx config invalid. Run: nginx -t"
    ERRORS=$((ERRORS + 1))
fi

# 4. Check ports
print_header "4. Network Ports"

print_check "Checking port 80 (Nginx)"
if netstat -tlnp 2>/dev/null | grep -q ":80"; then
    print_ok
else
    print_fail "Port 80 not listening"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking port 8000 (FastAPI)"
if netstat -tlnp 2>/dev/null | grep -q ":8000"; then
    print_ok
else
    print_fail "Port 8000 not listening"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking port 5432 (PostgreSQL)"
if netstat -tlnp 2>/dev/null | grep -q ":5432"; then
    print_ok
else
    print_fail "Port 5432 not listening"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking port 6379 (Redis)"
if netstat -tlnp 2>/dev/null | grep -q ":6379"; then
    print_ok
else
    print_fail "Port 6379 not listening"
    ERRORS=$((ERRORS + 1))
fi

# 5. Check database connectivity
print_header "5. Database Connectivity"

print_check "Checking PostgreSQL connection"
if docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -c "SELECT 1" &> /dev/null; then
    print_ok
else
    print_fail "Cannot connect to PostgreSQL"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking Redis connection"
if docker exec unigames-redis redis-cli ping &> /dev/null; then
    print_ok
else
    print_fail "Cannot connect to Redis"
    ERRORS=$((ERRORS + 1))
fi

# 6. Check database schema
print_header "6. Database Schema"

print_check "Checking database tables exist"
TABLE_COUNT=$(docker exec unigames-postgres psql -U scheduler_user -d scheduler_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -ge 8 ]; then
    echo -e "${GREEN}✓ OK${NC} ($TABLE_COUNT tables)"
else
    print_fail "Expected at least 8 tables, found $TABLE_COUNT"
    ERRORS=$((ERRORS + 1))
fi

# 7. Check HTTP endpoints
print_header "7. HTTP Endpoints"

print_check "Checking frontend (port 80)"
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
    print_ok
else
    print_fail "Frontend not responding on port 80"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking API health endpoint"
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    print_ok
else
    print_fail "API health check failed"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking API docs endpoint"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs | grep -q "200"; then
    print_ok
else
    print_fail "API docs not responding"
    ERRORS=$((ERRORS + 1))
fi

# 8. Check frontend build
print_header "8. Frontend Build"

print_check "Checking frontend dist directory exists"
if [ -d "/opt/unigames/frontend/dist" ]; then
    print_ok
else
    print_fail "Frontend not built. Run: cd /opt/unigames/frontend && npm run build"
    ERRORS=$((ERRORS + 1))
fi

print_check "Checking frontend index.html exists"
if [ -f "/opt/unigames/frontend/dist/index.html" ]; then
    print_ok
else
    print_fail "Frontend index.html missing"
    ERRORS=$((ERRORS + 1))
fi

# 9. Check logs
print_header "9. Recent Logs"

print_check "Checking for recent backend errors"
if [ -f "/var/log/unigames/backend-error.log" ]; then
    ERROR_COUNT=$(tail -n 100 /var/log/unigames/backend-error.log 2>/dev/null | grep -i error | wc -l | tr -d ' ')
    if [ "$ERROR_COUNT" -eq 0 ]; then
        print_ok
    else
        print_fail "Found $ERROR_COUNT recent errors in backend logs"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_ok
fi

# Summary
print_header "Verification Summary"

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ ALL CHECKS PASSED! ✓✓✓${NC}"
    echo ""
    echo "Deployment is successful! 🎉"
    echo ""
    echo "Application is available at:"
    echo "  - Frontend:  http://95.179.179.94"
    echo "  - API:       http://95.179.179.94/api"
    echo "  - API Docs:  http://95.179.179.94/api/docs"
    echo ""
    echo "Service management:"
    echo "  - Check status:  supervisorctl status unigames:*"
    echo "  - View logs:     tail -f /var/log/unigames/*.log"
    echo "  - Restart all:   supervisorctl restart unigames:*"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $ERRORS CHECK(S) FAILED${NC}"
    echo ""
    echo "Please fix the errors above."
    echo ""
    echo "Common fixes:"
    echo "  - Restart services:  supervisorctl restart unigames:*"
    echo "  - Restart Docker:    docker-compose restart"
    echo "  - Check logs:        tail -f /var/log/unigames/*.log"
    echo "  - Rebuild frontend:  cd /opt/unigames/frontend && npm run build"
    echo ""
    exit 1
fi
