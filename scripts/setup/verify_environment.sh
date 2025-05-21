#!/bin/bash
# Script to verify the Lucie project environment

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Verifying Lucie project environment...${NC}"

# Check required files and directories
echo -e "${BLUE}Checking required files and directories...${NC}"

# Function to check files and directories
check_path() {
  if [ -e "$1" ]; then
    echo -e "${GREEN}✓ $1 exists${NC}"
    return 0
  else
    echo -e "${RED}✗ $1 does not exist${NC}"
    return 1
  fi
}

# Check environment files
ENV_FILES=(".env" "backend/.env" "python-ai/.env" "lucie-ui/.env")
MISSING_ENV_FILES=0

for env_file in "${ENV_FILES[@]}"; do
  if ! check_path "$env_file"; then
    MISSING_ENV_FILES=$((MISSING_ENV_FILES+1))
  fi
done

if [ $MISSING_ENV_FILES -gt 0 ]; then
  echo -e "${YELLOW}Missing $MISSING_ENV_FILES environment files. Run ./scripts/setup/init_project.sh to create them.${NC}"
fi

# Check Docker and Docker Compose
echo -e "${BLUE}Checking Docker and Docker Compose...${NC}"
if command -v docker &> /dev/null; then
  DOCKER_VERSION=$(docker --version)
  echo -e "${GREEN}✓ Docker installed: $DOCKER_VERSION${NC}"
else
  echo -e "${RED}✗ Docker not installed${NC}"
fi

if command -v docker-compose &> /dev/null; then
  COMPOSE_VERSION=$(docker-compose --version)
  echo -e "${GREEN}✓ Docker Compose installed: $COMPOSE_VERSION${NC}"
else
  echo -e "${RED}✗ Docker Compose not installed${NC}"
fi

# Check Node.js
echo -e "${BLUE}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
  NODE_VERSION=$(node --version)
  echo -e "${GREEN}✓ Node.js installed: $NODE_VERSION${NC}"
  
  # Verify if version is at least 18
  NODE_MAJOR_VERSION=$(echo $NODE_VERSION | cut -d '.' -f 1 | tr -d 'v')
  if [ "$NODE_MAJOR_VERSION" -lt 18 ]; then
    echo -e "${YELLOW}⚠ Node.js version is older than recommended (18+)${NC}"
  fi
else
  echo -e "${RED}✗ Node.js not installed${NC}"
fi

# Check Python
echo -e "${BLUE}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
  PYTHON_VERSION=$(python3 --version)
  echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"
  
  # Verify if version is at least 3.11
  PYTHON_VERSION_NUM=$(echo $PYTHON_VERSION | cut -d ' ' -f 2)
  PYTHON_MAJOR=$(echo $PYTHON_VERSION_NUM | cut -d '.' -f 1)
  PYTHON_MINOR=$(echo $PYTHON_VERSION_NUM | cut -d '.' -f 2)
  
  if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${YELLOW}⚠ Python version is older than recommended (3.11+)${NC}"
  fi
else
  echo -e "${RED}✗ Python not installed${NC}"
fi

# Check Protocol Buffers compiler
echo -e "${BLUE}Checking Protocol Buffers compiler...${NC}"
if command -v protoc &> /dev/null; then
  PROTOC_VERSION=$(protoc --version)
  echo -e "${GREEN}✓ Protocol Buffers compiler installed: $PROTOC_VERSION${NC}"
else
  echo -e "${RED}✗ Protocol Buffers compiler not installed${NC}"
  echo -e "${YELLOW}Install with: sudo apt-get install protobuf-compiler${NC}"
fi

# Check if Protocol Buffer files are generated
echo -e "${BLUE}Checking Protocol Buffer generated files...${NC}"
NODE_PROTOS_DIR="backend/python-bridge/protos"
PYTHON_PROTOS_DIR="python-ai/grpc/protos"

if [ -d "$NODE_PROTOS_DIR" ] && [ "$(ls -A $NODE_PROTOS_DIR 2>/dev/null)" ]; then
  echo -e "${GREEN}✓ Node.js Protocol Buffer files generated${NC}"
else
  echo -e "${YELLOW}⚠ Node.js Protocol Buffer files not found. Run ./scripts/generate_protos.sh${NC}"
fi

if [ -d "$PYTHON_PROTOS_DIR" ] && [ "$(ls -A $PYTHON_PROTOS_DIR 2>/dev/null)" ]; then
  echo -e "${GREEN}✓ Python Protocol Buffer files generated${NC}"
else
  echo -e "${YELLOW}⚠ Python Protocol Buffer files not found. Run ./scripts/generate_protos.sh${NC}"
fi

echo -e "${BLUE}Environment verification complete!${NC}" 