#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Real-Time Chat Application Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Building Docker containers...${NC}"
docker compose build

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to build Docker containers.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker containers built successfully${NC}"
echo ""

echo -e "${YELLOW}Step 2: Starting containers...${NC}"
docker compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to start containers.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Containers started successfully${NC}"
echo ""

echo -e "${YELLOW}Step 3: Waiting for services to be ready...${NC}"
sleep 10

echo -e "${YELLOW}Step 4: Running database migrations...${NC}"
docker compose exec -T web python manage.py migrate

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to run migrations.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Migrations completed successfully${NC}"
echo ""

echo -e "${YELLOW}Step 5: Creating JWT token blacklist table...${NC}"
docker compose exec -T web python manage.py migrate token_blacklist

echo -e "${GREEN}✓ Token blacklist table created${NC}"
echo ""

echo -e "${YELLOW}Step 6: Checking health status...${NC}"
sleep 2
health_response=$(curl -s http://localhost:8000/health/)
echo "$health_response"
if echo "$health_response" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✓ All services are healthy${NC}"
else
    echo -e "${RED}⚠ Some services may have issues${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "The application is now running at:"
echo -e "  ${GREEN}API:${NC}          http://localhost:8000/api/"
echo -e "  ${GREEN}Admin Panel:${NC}  http://localhost:8000/admin/"
echo -e "  ${GREEN}Health Check:${NC} http://localhost:8000/health/"
echo ""
echo -e "WebSocket endpoint:"
echo -e "  ${GREEN}Chat:${NC}         ws://localhost:8000/ws/chat/<conversation_id>/"
echo ""
echo -e "To create a superuser, run:"
echo -e "  ${YELLOW}docker compose exec web python manage.py createsuperuser${NC}"
echo ""
echo -e "To run tests, run:"
echo -e "  ${YELLOW}docker compose exec web python manage.py test${NC}"
echo ""
echo -e "To view logs, run:"
echo -e "  ${YELLOW}docker compose logs -f web${NC}"
echo ""
echo -e "To stop the application, run:"
echo -e "  ${YELLOW}docker compose down${NC}"
echo ""

