#!/bin/bash

# FastAPI Development Server Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}Please update .env with your configuration${NC}"
fi

# Run the application
echo -e "${GREEN}Starting FastAPI application...${NC}"
echo -e "${GREEN}API Documentation: http://localhost:8000/docs${NC}"

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
