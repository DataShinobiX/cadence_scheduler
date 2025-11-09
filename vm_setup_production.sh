#!/bin/bash

###############################################################################
# UniGames Production Setup Script (Run on VM)
# This script sets up and starts all services on the production VM
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

APP_DIR="/opt/unigames"
LOG_DIR="/var/log/unigames"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}UniGames Production Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    exit 1
fi

cd $APP_DIR

# Create log directory
mkdir -p $LOG_DIR
chmod 755 $LOG_DIR

print_info "Step 1/10: Checking environment configuration..."
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_warning "Please ensure .env was included in deployment"
    exit 1
fi

# Update .env for production
print_info "Step 2/10: Updating environment for production..."
sed -i 's/DEBUG=true/DEBUG=false/' .env
sed -i 's/RELOAD=true/RELOAD=false/' .env
sed -i 's/WORKERS=1/WORKERS=4/' .env
sed -i 's|http://localhost:8000|http://95.179.179.94:8000|g' .env
sed -i 's|http://localhost:5173|http://95.179.179.94|g' .env

print_success "Environment configured for production"

# Setup Python virtual environment
print_info "Step 3/10: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_info "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

print_success "Python environment ready"

# Setup Docker containers (PostgreSQL + Redis)
print_info "Step 4/10: Starting Docker containers..."
docker-compose down 2>/dev/null || true
docker-compose up -d

print_info "Waiting for PostgreSQL to be ready..."
sleep 10

# Verify PostgreSQL is running
until docker exec unigames-postgres pg_isready -U scheduler_user -d scheduler_db > /dev/null 2>&1; do
    print_info "Waiting for PostgreSQL..."
    sleep 2
done

print_success "PostgreSQL is ready"

# Verify Redis is running
until docker exec unigames-redis redis-cli ping > /dev/null 2>&1; do
    print_info "Waiting for Redis..."
    sleep 2
done

print_success "Redis is ready"

# Setup database
print_info "Step 5/10: Setting up database schema..."
chmod +x setup_database.sh
./setup_database.sh

print_success "Database schema created"

# Setup authentication database
print_info "Step 6/10: Setting up authentication tables..."
chmod +x setup_auth_db.sh
./setup_auth_db.sh

print_success "Authentication tables created"

# Build frontend
print_info "Step 7/10: Building frontend..."
cd frontend

print_info "Installing frontend dependencies..."
npm install --quiet

print_info "Building production bundle..."
npm run build

print_success "Frontend built successfully"

cd $APP_DIR

# Configure Nginx
print_info "Step 8/10: Configuring Nginx..."
cat > /etc/nginx/sites-available/unigames << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend (React build)
    location / {
        root /opt/unigames/frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Increase timeouts for LLM processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    client_max_body_size 10M;
}
EOF

ln -sf /etc/nginx/sites-available/unigames /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx

print_success "Nginx configured and started"

# Configure Supervisor for process management
print_info "Step 9/10: Configuring Supervisor for process management..."

cat > /etc/supervisor/conf.d/unigames.conf << EOF
# FastAPI Backend
[program:unigames-backend]
directory=$APP_DIR
command=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
autostart=true
autorestart=true
stderr_logfile=$LOG_DIR/backend-error.log
stdout_logfile=$LOG_DIR/backend.log
user=root
environment=PATH="$APP_DIR/venv/bin"

# Celery Worker
[program:unigames-celery-worker]
directory=$APP_DIR
command=$APP_DIR/venv/bin/celery -A app.celery_app worker --loglevel=info --concurrency=4
autostart=true
autorestart=true
stderr_logfile=$LOG_DIR/celery-worker-error.log
stdout_logfile=$LOG_DIR/celery-worker.log
user=root
stopwaitsecs=600
environment=PATH="$APP_DIR/venv/bin"

# Celery Beat (Scheduler)
[program:unigames-celery-beat]
directory=$APP_DIR
command=$APP_DIR/venv/bin/celery -A app.celery_app beat --loglevel=info
autostart=true
autorestart=true
stderr_logfile=$LOG_DIR/celery-beat-error.log
stdout_logfile=$LOG_DIR/celery-beat.log
user=root
environment=PATH="$APP_DIR/venv/bin"

# Group all services
[group:unigames]
programs=unigames-backend,unigames-celery-worker,unigames-celery-beat
EOF

supervisorctl reread
supervisorctl update

print_success "Supervisor configured"

# Start all services
print_info "Step 10/10: Starting all services..."
supervisorctl start unigames:*

print_success "All services started"

# Wait a moment for services to initialize
sleep 5

# Check service status
print_info "Checking service status..."
supervisorctl status unigames:*

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Production Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service URLs:"
echo "  - Frontend:  http://95.179.179.94"
echo "  - API:       http://95.179.179.94/api"
echo "  - API Docs:  http://95.179.179.94/api/docs"
echo ""
echo "Service Management Commands:"
echo "  - Check status:    supervisorctl status unigames:*"
echo "  - Stop all:        supervisorctl stop unigames:*"
echo "  - Start all:       supervisorctl start unigames:*"
echo "  - Restart all:     supervisorctl restart unigames:*"
echo "  - View logs:       tail -f $LOG_DIR/*.log"
echo ""
echo "Database Management:"
echo "  - PostgreSQL:      docker exec -it unigames-postgres psql -U scheduler_user -d scheduler_db"
echo "  - Redis:           docker exec -it unigames-redis redis-cli"
echo ""
echo "Email Agent Status:"
echo "  - Worker:          supervisorctl status unigames:unigames-celery-worker"
echo "  - Beat Scheduler:  supervisorctl status unigames:unigames-celery-beat"
echo "  - Check logs:      tail -f $LOG_DIR/celery-*.log"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "1. Update Google OAuth redirect URI to: http://95.179.179.94:8000/api/v1/auth/callback"
echo "2. Ensure all API keys in .env are valid"
echo "3. Test the application at: http://95.179.179.94"
echo ""
print_success "Deployment successful! 🎉"
