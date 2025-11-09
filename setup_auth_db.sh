#!/bin/bash

###############################################################################
# Authentication Database Setup Script
# Run this script to set up the auth_sessions table for authentication
###############################################################################

set -e  # Exit on error

echo "=========================================="
echo "Setting up Authentication Database"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Find the database container
DB_CONTAINER=$(docker ps --filter "ancestor=postgres:15-alpine" --format "{{.Names}}" | head -n 1)

if [ -z "$DB_CONTAINER" ]; then
    echo -e "${RED}❌ Error: PostgreSQL container not found. Please run 'docker-compose up -d' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found database container: $DB_CONTAINER${NC}"
echo ""

# Create auth_sessions table
echo "Creating auth_sessions table..."
docker exec -i "$DB_CONTAINER" psql -U scheduler_user -d scheduler_db << 'EOF'

-- Create auth_sessions table if it doesn't exist
CREATE TABLE IF NOT EXISTS auth_sessions (
    session_token UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token
    ON auth_sessions(session_token) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user
    ON auth_sessions(user_id) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires
    ON auth_sessions(expires_at) WHERE is_active = true;

-- Display table structure
\d auth_sessions

EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ auth_sessions table created successfully!${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to create auth_sessions table${NC}"
    exit 1
fi

# Verify table exists
echo "Verifying table..."
TABLE_EXISTS=$(docker exec -i "$DB_CONTAINER" psql -U scheduler_user -d scheduler_db -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'auth_sessions');")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ Verification successful! auth_sessions table is ready.${NC}"
    echo ""
else
    echo -e "${RED}❌ Verification failed. Table was not created.${NC}"
    exit 1
fi

# Count sessions
SESSION_COUNT=$(docker exec -i "$DB_CONTAINER" psql -U scheduler_user -d scheduler_db -tAc "SELECT COUNT(*) FROM auth_sessions;")
echo -e "Current sessions in database: ${YELLOW}$SESSION_COUNT${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}✅ Authentication Database Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the backend: ./run_backend.sh"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Visit http://localhost:5173 and sign up!"
echo ""
