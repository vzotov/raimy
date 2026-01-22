#!/bin/bash

# Deploy from GitHub instead of local files
# Usage: ./deploy-from-github.sh [branch-name] [no-cache]
#
# Examples:
#   ./deploy-from-github.sh              # Deploy dev branch (uses Docker cache)
#   ./deploy-from-github.sh main         # Deploy main branch
#   ./deploy-from-github.sh dev no-cache # Deploy dev with full rebuild (no cache)
#
# This pulls code directly from GitHub on the VM, ensuring:
# - Only committed code is deployed
# - Consistent deployments
# - No local uncommitted changes
# - No macOS metadata corruption (null bytes issue)

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
ZONE="us-east1-b"
INSTANCE_NAME="raimy-backend"
BRANCH="${1:-dev}"  # Default to dev branch, or use argument
NO_CACHE="${2:-}"   # Pass "no-cache" as second arg for clean rebuild
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
gcloud compute ssh "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --command="mkdir -p ~/raimy"
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
        BRANCH='${BRANCH}'
        REPO_URL='${REPO_URL}'

        # Clone or pull repository
        if [ -d ~/raimy-github ]; then
            echo 'Repository exists, pulling latest changes...'
            cd ~/raimy-github
            git fetch origin
            git checkout \"\$BRANCH\"
            git pull origin \"\$BRANCH\"
        else
            echo 'Cloning repository...'
            git clone \"\$REPO_URL\" ~/raimy-github
            cd ~/raimy-github
            git checkout \"\$BRANCH\"
        fi

        # Copy to deployment directory (preserve .env)
        echo 'Copying to deployment directory...'
        rsync -av --delete \
            --exclude='.git' \
            --exclude='client/node_modules' \
            --exclude='client/.next' \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.env' \
            ~/raimy-github/ ~/raimy/
    "
echo -e "${GREEN}✓ Code pulled from GitHub${NC}"

echo -e "${YELLOW}Step 3: Rebuilding and restarting services...${NC}"
if [ "$NO_CACHE" = "no-cache" ]; then
    echo -e "${YELLOW}Using --no-cache for clean rebuild${NC}"
    gcloud compute ssh "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --command="cd ~/raimy && docker-compose -f docker-compose.prod.yml build --no-cache && docker-compose -f docker-compose.prod.yml up -d"
else
    gcloud compute ssh "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --command="cd ~/raimy && docker-compose -f docker-compose.prod.yml up -d --build"
fi
echo -e "${GREEN}✓ Services restarted${NC}"

echo -e "${YELLOW}Step 4: Verifying deployment...${NC}"
gcloud compute ssh "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --project="${PROJECT_ID}" \
    --command="
        echo 'Checking migration status...'
        docker logs \$(docker ps -q -f name=raimy-api) 2>&1 | grep -E '(migration|Migration|alembic|✅|❌)' | tail -5
        echo ''
        echo 'Service health:'
        docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(raimy|postgres|redis)'
    "
echo -e "${GREEN}✓ Deployment verified${NC}"

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