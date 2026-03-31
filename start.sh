#!/bin/bash

# Regulatory Risk Analysis System v2.0 - Startup Script
# ======================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     REGULATORY RISK ANALYSIS SYSTEM v2.0                       ║"
echo "║     Advanced Risk Modeling & Regulatory Compliance             ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create required directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p uploads reports data logs
echo -e "${GREEN}✓ Directories created${NC}"

# Check if we should use Docker
if [ "$1" == "docker" ]; then
    echo -e "${BLUE}Starting with Docker Compose...${NC}"
    cd docker
    docker-compose up --build -d
    echo -e "${GREEN}✓ Services started${NC}"
    echo -e "${BLUE}API: http://localhost:8000${NC}"
    echo -e "${BLUE}Frontend: http://localhost${NC}"
    exit 0
fi

# Function to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    
    if [ -n "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

trap cleanup INT TERM

# Start Backend API
echo ""
echo -e "${BLUE}Starting Backend API...${NC}"
cd backend/api

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(dirname $(pwd))"

# Start API with auto-reload in development
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir .. \
    --log-level info > ../../logs/api.log 2>&1 &

API_PID=$!
cd ../..

echo -e "${GREEN}✓ API started (PID: $API_PID)${NC}"
echo -e "${BLUE}  → API URL: http://localhost:8000${NC}"
echo -e "${BLUE}  → API Docs: http://localhost:8000/docs${NC}"

# Wait for API to be ready
echo ""
echo -e "${YELLOW}Waiting for API to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Start Frontend
echo ""
echo -e "${BLUE}Starting Frontend...${NC}"
cd frontend

# Use Python's built-in server
python3 -m http.server 8080 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}  → Frontend URL: http://localhost:8080${NC}"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  System is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}Frontend:${NC} http://localhost:8080"
echo -e "  ${BLUE}API:${NC}      http://localhost:8000"
echo -e "  ${BLUE}Docs:${NC}     http://localhost:8000/docs"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running
wait
