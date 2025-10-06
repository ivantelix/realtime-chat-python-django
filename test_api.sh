#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}API Testing Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
echo -e "${YELLOW}GET ${BASE_URL}/health/${NC}"
response=$(curl -s -w "\n%{http_code}" ${BASE_URL}/health/)
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "Response Code: $http_code"
echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
echo ""

# Test 2: Register User 1
echo -e "${BLUE}Test 2: Register User 1${NC}"
echo -e "${YELLOW}POST ${BASE_URL}/api/users/register/${NC}"
user1_data='{
  "username": "alice",
  "email": "alice@example.com",
  "password": "SecurePass123!",
  "first_name": "Alice",
  "last_name": "Smith"
}'
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/users/register/ \
  -H "Content-Type: application/json" \
  -d "$user1_data")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "Response Code: $http_code"
echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
echo ""

# Test 3: Register User 2
echo -e "${BLUE}Test 3: Register User 2${NC}"
echo -e "${YELLOW}POST ${BASE_URL}/api/users/register/${NC}"
user2_data='{
  "username": "bob",
  "email": "bob@example.com",
  "password": "SecurePass456!",
  "first_name": "Bob",
  "last_name": "Johnson"
}'
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/users/register/ \
  -H "Content-Type: application/json" \
  -d "$user2_data")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "Response Code: $http_code"
echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
echo ""

# Test 4: Login User 1
echo -e "${BLUE}Test 4: Login User 1 (Alice)${NC}"
echo -e "${YELLOW}POST ${BASE_URL}/api/users/login/${NC}"
login_data='{
  "username": "alice",
  "password": "SecurePass123!"
}'
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/users/login/ \
  -H "Content-Type: application/json" \
  -d "$login_data")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "Response Code: $http_code"
echo "$body" | python -m json.tool 2>/dev/null || echo "$body"

# Extract access token
access_token=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin).get('access', ''))" 2>/dev/null)
user1_id=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin).get('user', {}).get('id', ''))" 2>/dev/null)

echo ""

# Test 5: Get User Profile
echo -e "${BLUE}Test 5: Get User Profile${NC}"
echo -e "${YELLOW}GET ${BASE_URL}/api/users/profile/${NC}"
if [ ! -z "$access_token" ]; then
    response=$(curl -s -w "\n%{http_code}" -X GET ${BASE_URL}/api/users/profile/ \
      -H "Authorization: Bearer $access_token")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    echo "Response Code: $http_code"
    echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}Skipped: No access token available${NC}"
fi
echo ""

# Test 6: Login User 2
echo -e "${BLUE}Test 6: Login User 2 (Bob)${NC}"
echo -e "${YELLOW}POST ${BASE_URL}/api/users/login/${NC}"
login_data2='{
  "username": "bob",
  "password": "SecurePass456!"
}'
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/users/login/ \
  -H "Content-Type: application/json" \
  -d "$login_data2")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "Response Code: $http_code"
user2_id=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin).get('user', {}).get('id', ''))" 2>/dev/null)
echo ""

# Test 7: Create Conversation
echo -e "${BLUE}Test 7: Create Conversation${NC}"
echo -e "${YELLOW}POST ${BASE_URL}/api/chat/conversations/${NC}"
if [ ! -z "$access_token" ] && [ ! -z "$user2_id" ]; then
    conv_data="{\"participants\": [$user2_id]}"
    response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/chat/conversations/ \
      -H "Authorization: Bearer $access_token" \
      -H "Content-Type: application/json" \
      -d "$conv_data")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    echo "Response Code: $http_code"
    echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
    
    conversation_id=$(echo "$body" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
else
    echo -e "${RED}Skipped: Missing required data${NC}"
fi
echo ""

# Test 8: List Conversations
echo -e "${BLUE}Test 8: List Conversations${NC}"
echo -e "${YELLOW}GET ${BASE_URL}/api/chat/conversations/${NC}"
if [ ! -z "$access_token" ]; then
    response=$(curl -s -w "\n%{http_code}" -X GET ${BASE_URL}/api/chat/conversations/ \
      -H "Authorization: Bearer $access_token")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    echo "Response Code: $http_code"
    echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}Skipped: No access token available${NC}"
fi
echo ""

# Test 9: Get Conversation Messages
echo -e "${BLUE}Test 9: Get Conversation Messages${NC}"
if [ ! -z "$access_token" ] && [ ! -z "$conversation_id" ]; then
    echo -e "${YELLOW}GET ${BASE_URL}/api/chat/conversations/${conversation_id}/messages/${NC}"
    response=$(curl -s -w "\n%{http_code}" -X GET ${BASE_URL}/api/chat/conversations/${conversation_id}/messages/ \
      -H "Authorization: Bearer $access_token")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    echo "Response Code: $http_code"
    echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}Skipped: Missing conversation ID or access token${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}API Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "For WebSocket testing, you can use tools like:"
echo -e "  - wscat: ${YELLOW}wscat -c ws://localhost:8000/ws/chat/${conversation_id}/${NC}"
echo -e "  - Postman"
echo -e "  - Browser console with JavaScript WebSocket API"
echo ""

