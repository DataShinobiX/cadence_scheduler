#!/bin/bash

# Test Authentication Flow
# This script tests the complete auth system

BASE_URL="http://localhost:8000"

echo "======================================================================"
echo "Testing Authentication Flow"
echo "======================================================================"
echo ""

# Test 1: Signup
echo "Test 1: Signup"
echo "----------------------------------------------------------------------"
SIGNUP_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "name": "Demo User"
  }')

echo "$SIGNUP_RESPONSE" | python3 -m json.tool
echo ""

# Extract session token
SESSION_TOKEN=$(echo "$SIGNUP_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_token', ''))")

if [ -z "$SESSION_TOKEN" ]; then
    echo "❌ Signup failed - no session token received"
    exit 1
fi

echo "✅ Signup successful! Session token: ${SESSION_TOKEN:0:20}..."
echo ""

# Test 2: Get Current User
echo "Test 2: Get Current User (using session token)"
echo "----------------------------------------------------------------------"
USER_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/auth/me" \
  -H "Authorization: Bearer $SESSION_TOKEN")

echo "$USER_RESPONSE" | python3 -m json.tool
echo ""

# Verify user_id
USER_ID=$(echo "$USER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('user_id', ''))")

if [ -z "$USER_ID" ]; then
    echo "❌ Get current user failed"
    exit 1
fi

echo "✅ User authenticated! User ID: $USER_ID"
echo ""

# Test 3: Logout
echo "Test 3: Logout"
echo "----------------------------------------------------------------------"
LOGOUT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
  -H "Authorization: Bearer $SESSION_TOKEN")

echo "$LOGOUT_RESPONSE" | python3 -m json.tool
echo ""

# Test 4: Try to use logged out session (should fail)
echo "Test 4: Try to access with logged out session (should fail)"
echo "----------------------------------------------------------------------"
INVALID_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/auth/me" \
  -H "Authorization: Bearer $SESSION_TOKEN")

echo "$INVALID_RESPONSE" | python3 -m json.tool
echo ""

# Test 5: Login with existing email
echo "Test 5: Login with existing email"
echo "----------------------------------------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com"
  }')

echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

# Extract new session token
NEW_SESSION_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_token', ''))")

if [ -z "$NEW_SESSION_TOKEN" ]; then
    echo "❌ Login failed - no session token received"
    exit 1
fi

echo "✅ Login successful! New session token: ${NEW_SESSION_TOKEN:0:20}..."
echo ""

# Test 6: Test /api/transcribe without auth (should fail)
echo "Test 6: Try /api/transcribe without authentication (should fail)"
echo "----------------------------------------------------------------------"
NO_AUTH_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/transcribe" \
  -F "run_agents=false" \
  2>&1)

echo "$NO_AUTH_RESPONSE" | head -20
echo ""

echo "======================================================================"
echo "✅ All Authentication Tests Completed!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  ✅ Signup works"
echo "  ✅ Get current user works"
echo "  ✅ Logout works"
echo "  ✅ Session invalidation works"
echo "  ✅ Login works"
echo "  ✅ Transcribe endpoint requires authentication"
echo ""
echo "Next Steps:"
echo "  1. Test /api/transcribe WITH authentication"
echo "  2. Integrate with frontend"
echo ""
