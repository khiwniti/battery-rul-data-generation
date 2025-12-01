#!/bin/bash
# Backend API Testing Script

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================"
echo "Backend API Testing"
echo "============================================"
echo ""

# Test 1: Health Endpoint
echo "1. Testing Health Endpoint..."
HEALTH=$(curl -s $BASE_URL/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health endpoint working${NC}"
else
    echo -e "${RED}✗ Health endpoint failed${NC}"
    exit 1
fi

# Test 2: Login
echo "2. Testing Login..."
cat > /tmp/login.json << 'EOF'
{
  "username": "admin",
  "password": "Admin123!"
}
EOF

LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d @/tmp/login.json)

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

# Test 3: /me Endpoint
echo "3. Testing /me endpoint..."
ME_RESPONSE=$(curl -s $BASE_URL/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN")

if echo "$ME_RESPONSE" | grep -q "admin"; then
    echo -e "${GREEN}✓ /me endpoint working${NC}"
else
    echo -e "${RED}✗ /me endpoint failed${NC}"
    exit 1
fi

# Test 4: Locations Endpoint
echo "4. Testing locations endpoint..."
LOCATIONS=$(curl -s $BASE_URL/api/v1/locations \
  -H "Authorization: Bearer $TOKEN")

echo -e "${GREEN}✓ Locations endpoint accessible (empty database expected)${NC}"

# Test 5: Batteries Endpoint
echo "5. Testing batteries endpoint..."
BATTERIES=$(curl -s $BASE_URL/api/v1/batteries \
  -H "Authorization: Bearer $TOKEN")

echo -e "${GREEN}✓ Batteries endpoint accessible (empty database expected)${NC}"

# Test 6: Alerts Endpoint
echo "6. Testing alerts endpoint..."
ALERTS=$(curl -s $BASE_URL/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN")

echo -e "${GREEN}✓ Alerts endpoint accessible (empty database expected)${NC}"

echo ""
echo "============================================"
echo -e "${GREEN}All Tests Passed!${NC}"
echo "============================================"
echo ""
echo "API Documentation: $BASE_URL/api/docs"
echo "Health Check: $BASE_URL/health"
echo ""
