#!/bin/bash

# Deploy from GitHub instead of local files
# Usage: ./deploy-from-github.sh [branch-name]
#
# This pulls code directly from GitHub on the VM, ensuring:
# - Only committed code is deployed
# - Consistent deployments
# - No local uncommitted changes

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
ZONE="us-east1-b"
INSTANCE_NAME="raimy-backend"
BRANCH="${1:-dev}"  # Default to dev branch, or use argument
REPO_URL="https://github.com/vzotov/raimy.git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Deploying from GitHub ===${NC}"
echo -e "${GREEN}Branch: ${BRANCH}${NC}"
echo -e "${GREEN}Repository: ${REPO_URL}${NC}"
echo ""

# Check if .env.prod exists
if [ ! -f "../.env.prod" ]; then
    echo -e "${RED}Error: .env.prod file not found!${NC}"
    echo "Please create .env.prod from .env.prod.example"
    exit 1
fi

echo -e "${YELLOW}Step 1: Uploading .env.prod to VM...${NC}"
gcloud compute scp --zone="${ZONE}" \
    ../.env.prod "${INSTANCE_NAME}":~/raimy/.env \
    --project="${PROJECT_ID}"
echo -e "${GREEN}✓ Environment file uploaded${NC}"

echo -e "${YELLOW}Step 2: Pulling code from GitHub on VM...${NC}"
gcloud compute ssh "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --command="
        set -e

        # Clone or pull repository
        if [ -d ~/raimy-github ]; then
            echo 'Repository exists, pulling latest changes...'
            cd ~/raimy-github
            git fetch origin
            git checkout ${BRANCH}
            git pull origin ${BRANCH}
        else
            echo 'Cloning repository...'
            git clone ${REPO_URL} ~/raimy-github
            cd ~/raimy-github
            git checkout ${BRANCH}
        fi

        # Copy to deployment directory
        echo 'Copying to deployment directory...'
        rsync -av --delete \
            --exclude='.git' \
            --exclude='client/node_modules' \
            --exclude='client/.next' \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            ~/raimy-github/ ~/raimy/

        # Restore .env file (not in git)
        cp ~/raimy/.env ~/raimy/.env 2>/dev/null || true
    "
echo -e "${GREEN}✓ Code pulled from GitHub${NC}"

echo -e "${YELLOW}Step 3: Rebuilding and restarting services...${NC}"
gcloud compute ssh "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --command="
        cd ~/raimy
        docker-compose -f docker-compose.prod.yml up -d --build
    "
echo -e "${GREEN}✓ Services restarted${NC}"

# Get VM IP
VM_IP=$(gcloud compute instances describe "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Deployed from: ${REPO_URL} (branch: ${BRANCH})"
echo "API Endpoint: http://${VM_IP}/api"
echo ""
echo "View logs: ./gcp-vm-deploy.sh logs"