#!/bin/bash

###############################################################################
# UniGames Intelligent Scheduler - VM Deployment Script
# This script deploys the application to the hackathon VM
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# VM Details
VM_HOST="95.179.179.94"
VM_USER="root"
APP_DIR="/opt/unigames"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}UniGames VM Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we can connect to VM
print_info "Testing SSH connection to VM..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${VM_USER}@${VM_HOST} "echo 'Connection successful'" 2>/dev/null; then
    print_success "SSH connection successful"
else
    print_error "Cannot connect to VM. Please check credentials."
    echo ""
    echo "Quick command: ssh ${VM_USER}@${VM_HOST}"
    echo "Password: K5v-n]r=n6RTK\$Re"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_warning "Please create .env file with all required credentials"
    print_warning "Copy from .env.example and fill in your API keys"
    exit 1
fi

# Verify critical environment variables
print_info "Checking environment variables..."
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    print_error "OPENAI_API_KEY not set in .env file"
    exit 1
fi

if [ -z "$GOOGLE_CLIENT_ID" ] || [ "$GOOGLE_CLIENT_ID" = "your-client-id.apps.googleusercontent.com" ]; then
    print_error "GOOGLE_CLIENT_ID not set in .env file"
    exit 1
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ] || [ "$GOOGLE_CLIENT_SECRET" = "your-client-secret" ]; then
    print_error "GOOGLE_CLIENT_SECRET not set in .env file"
    exit 1
fi

print_success "Environment variables validated"

# Create deployment package
print_info "Creating deployment package..."
TEMP_DIR=$(mktemp -d)
DEPLOY_ARCHIVE="${TEMP_DIR}/unigames_deploy.tar.gz"

# Files and directories to include
tar -czf "$DEPLOY_ARCHIVE" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='chroma_data' \
    --exclude='frontend/dist' \
    --exclude='frontend/node_modules' \
    --exclude='.env.local' \
    .

print_success "Deployment package created: $(du -h $DEPLOY_ARCHIVE | cut -f1)"

# Upload to VM
print_info "Uploading application to VM..."
scp -o StrictHostKeyChecking=no "$DEPLOY_ARCHIVE" ${VM_USER}@${VM_HOST}:/tmp/unigames_deploy.tar.gz

print_success "Upload complete"

# Execute deployment on VM
print_info "Executing deployment on VM..."
ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_HOST} bash << 'ENDSSH'
    set -e

    echo "================================================"
    echo "Installing dependencies on VM..."
    echo "================================================"

    # Update system packages
    apt-get update -qq

    # Install required packages
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        docker.io \
        docker-compose \
        nginx \
        curl \
        git \
        supervisor \
        postgresql-client \
        redis-tools

    # Start Docker
    systemctl start docker
    systemctl enable docker

    # Install Node.js 18
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi

    echo "Node version: $(node --version)"
    echo "npm version: $(npm --version)"
    echo "Python version: $(python3 --version)"
    echo "Docker version: $(docker --version)"

    # Create application directory
    mkdir -p /opt/unigames
    cd /opt/unigames

    # Extract application
    echo "Extracting application..."
    tar -xzf /tmp/unigames_deploy.tar.gz -C /opt/unigames

    # Clean up
    rm /tmp/unigames_deploy.tar.gz

    echo "================================================"
    echo "Deployment files extracted to /opt/unigames"
    echo "================================================"
ENDSSH

print_success "Deployment successful!"

# Copy production setup script
print_info "Copying production setup script to VM..."
scp -o StrictHostKeyChecking=no ./vm_setup_production.sh ${VM_USER}@${VM_HOST}:${APP_DIR}/

print_success "Setup script copied"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. SSH into the VM:"
echo "   ssh ${VM_USER}@${VM_HOST}"
echo ""
echo "2. Navigate to application directory:"
echo "   cd ${APP_DIR}"
echo ""
echo "3. Run production setup:"
echo "   chmod +x vm_setup_production.sh"
echo "   ./vm_setup_production.sh"
echo ""
echo "4. Application will be available at:"
echo "   http://${VM_HOST}"
echo ""
echo -e "${YELLOW}Note: Make sure to update GOOGLE_REDIRECT_URI in .env to:${NC}"
echo -e "${YELLOW}      http://${VM_HOST}:8000/api/v1/auth/callback${NC}"
echo ""

# Cleanup
rm -rf "$TEMP_DIR"
