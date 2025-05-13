#!/bin/bash
set -e

# Deployment script for Ingren LLM Email API
# This script will:
# 1. Create a deployment package using Poetry
# 2. Run Pulumi to deploy to AWS

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== Ingren LLM Email API Deployment =====${NC}"

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set.${NC}"
    echo "Please set it before deploying:"
    echo "export OPENAI_API_KEY=your-api-key"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured or invalid.${NC}"
    echo "Please configure your AWS credentials:"
    echo "aws configure"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry is not installed.${NC}"
    echo "Please install Poetry first: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Ask for confirmation before proceeding
read -p "Continue with deployment to AWS? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

echo -e "${YELLOW}Starting deployment...${NC}"

# Step 2: Create deployment package
echo -e "${GREEN}Creating deployment package...${NC}"
# Clean previous deployment package if it exists
rm -rf deployment_package
mkdir -p deployment_package

# Copy application files
cp -r src deployment_package/
cp -r prompts deployment_package/
cp lambda_handler.py deployment_package/

# Install dependencies into the deployment package
pip install -r requirements.txt --platform manylinux2014_x86_64 --target deployment_package/ --python-version 3.11 --only-binary=:all:

# Step 4: Change to infrastructure directory and run Pulumi
echo -e "${GREEN}Running Pulumi deployment...${NC}"

# Install Pulumi plugin and dependencies
echo -e "${GREEN}Installing Pulumi dependencies...${NC}"

# Run Pulumi up with Poetry's Python
echo -e "${GREEN}Deploying to AWS...${NC}"
poetry run pulumi up -C infrastructure

# Get the API endpoint and API key from Pulumi outputs
API_ENDPOINT=$(pulumi stack output generate_email_endpoint)
API_KEY=$(pulumi stack output api_key_value)

# Go back to the root directory
cd ..

echo -e "${GREEN}===== Deployment Complete =====${NC}"
echo -e "API Endpoint: ${YELLOW}$API_ENDPOINT${NC}"
echo -e "API Key: ${YELLOW}$API_KEY${NC}"
echo
echo -e "To test your API, run:"
echo -e "${YELLOW}curl -X POST $API_ENDPOINT \\"
echo -e "  -H \"Content-Type: application/json\" \\"
echo -e "  -H \"x-api-key: $API_KEY\" \\"
echo -e "  -d '{\"prospect\":{\"first_name\":\"Test\",\"last_name\":\"User\",\"job_title\":\"CTO\"},\"company\":{\"company_name\":\"Test Company\"}}'"${NC}

echo
echo -e "${GREEN}To destroy the deployment:${NC}"
echo -e "${YELLOW}cd infrastructure && pulumi destroy${NC}"