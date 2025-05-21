#!/bin/bash
# Script to initialize the Lucie project environment

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Initializing Lucie project environment...${NC}"

# Check if running from the project root
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "python-ai" ]; then
  echo -e "${RED}Error: This script must be run from the project root directory${NC}"
  echo -e "${YELLOW}Please cd to the project root and run: ./scripts/setup/init_project.sh${NC}"
  exit 1
fi

# Create environment files if they don't exist
echo -e "${BLUE}Setting up environment files...${NC}"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo -e "${YELLOW}Creating .env from .env.example${NC}"
  cp .env.example .env
fi

if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
  echo -e "${YELLOW}Creating backend/.env from backend/.env.example${NC}"
  cp backend/.env.example backend/.env
fi

if [ ! -f "python-ai/.env" ] && [ -f "python-ai/.env.example" ]; then
  echo -e "${YELLOW}Creating python-ai/.env from python-ai/.env.example${NC}"
  cp python-ai/.env.example python-ai/.env
fi

if [ ! -f "lucie-ui/.env" ] && [ -f "lucie-ui/.env.example" ]; then
  echo -e "${YELLOW}Creating lucie-ui/.env from lucie-ui/.env.example${NC}"
  cp lucie-ui/.env.example lucie-ui/.env
fi

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p backend/logs
mkdir -p python-ai/logs
mkdir -p backend/python-bridge/protos
mkdir -p python-ai/grpc/protos

# Generate Protocol Buffers
echo -e "${BLUE}Generating Protocol Buffer files...${NC}"
if [ -f "scripts/generate_protos.sh" ]; then
  chmod +x scripts/generate_protos.sh
  ./scripts/generate_protos.sh
else
  echo -e "${RED}Error: Protocol Buffer generation script not found${NC}"
fi

# Make dev.sh executable
if [ -f "dev.sh" ]; then
  echo -e "${BLUE}Making dev.sh executable...${NC}"
  chmod +x dev.sh
fi

echo -e "${GREEN}Project initialization complete!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Review and update your .env files with appropriate values"
echo -e "2. Start the development environment: ${YELLOW}./dev.sh start${NC}"
echo -e "3. Visit the UI at ${YELLOW}http://localhost:3000${NC} when ready" 