#!/bin/bash

# Voice Agent Platform - Run Script
# This script ensures the application runs from the correct directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Voice Agent Platform...${NC}"

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found.${NC}"
    echo -e "${YELLOW}Please run this script from the project root directory.${NC}"
    echo -e "${YELLOW}Current directory: $(pwd)${NC}"
    exit 1
fi

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Error: Poetry is not installed.${NC}"
    echo -e "${YELLOW}Please install Poetry first: https://python-poetry.org/docs/#installation${NC}"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Installing dependencies...${NC}"
    poetry install
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${YELLOW}📝 Please edit .env file with your configuration:${NC}"
        echo -e "${YELLOW}   - LIVEKIT_URL${NC}"
        echo -e "${YELLOW}   - LIVEKIT_API_KEY${NC}"
        echo -e "${YELLOW}   - LIVEKIT_API_SECRET${NC}"
        echo -e "${YELLOW}   - SIP_OUTBOUND_TRUNK_ID${NC}"
        echo -e "${YELLOW}   - OPENAI_API_KEY${NC}"
    else
        echo -e "${RED}❌ Error: env.example file not found.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Environment ready!${NC}"
echo -e "${BLUE}🌐 Starting server at http://localhost:8000${NC}"
echo -e "${BLUE}📚 API Documentation: http://localhost:8000/docs${NC}"
echo -e "${BLUE}🏥 Health Check: http://localhost:8000/health${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the application
poetry run python -m app.main --port 8000 