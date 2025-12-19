#!/bin/bash

# Cloud Run Deployment Script for Raimy Backend Services
# Usage: ./deploy.sh [service-name] or ./deploy.sh all
#
# Prerequisites:
# 1. gcloud CLI installed and authenticated
# 2. GCP project created and selected
# 3. Cloud Run API enabled
# 4. .env.prod file configured

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-east1"  # Free tier region
ENV_FILE="../.env.prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.prod exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env.prod file not found!${NC}"
    echo "Please create .env.prod from .env.prod.example"
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

echo -e "${GREEN}Deploying to GCP Project: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Region: ${REGION}${NC}"
echo ""

# Function to deploy a service
deploy_service() {
    local SERVICE_NAME=$1
    local DOCKERFILE_PATH=$2
    local DOCKERFILE=$3
    local PORT=$4
    local CMD=$5

    echo -e "${YELLOW}Deploying ${SERVICE_NAME}...${NC}"

    # Build and submit to Cloud Build
    gcloud builds submit \
        --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
        --project="${PROJECT_ID}" \
        "${DOCKERFILE_PATH}" \
        --dockerfile="${DOCKERFILE}"

    # Deploy to Cloud Run with command override
    gcloud run deploy "${SERVICE_NAME}" \
        --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
        --platform managed \
        --region "${REGION}" \
        --allow-unauthenticated \
        --port "${PORT}" \
        --memory 512Mi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 10 \
        --timeout 300 \
        --command "${CMD}" \
        --set-env-vars "PYTHONPATH=/app/server,DATABASE_URL=${DATABASE_URL},REDIS_URL=${REDIS_URL},OPENAI_API_KEY=${OPENAI_API_KEY},SERVICE_API_KEY=${SERVICE_API_KEY},AUTO_MIGRATE=${AUTO_MIGRATE:-true}" \
        --project="${PROJECT_ID}"

    echo -e "${GREEN}✓ ${SERVICE_NAME} deployed successfully!${NC}"
    echo ""
}

# Function to set service-to-service URLs
update_service_urls() {
    echo -e "${YELLOW}Updating service-to-service URLs...${NC}"

    # Get service URLs
    AUTH_URL=$(gcloud run services describe auth-service --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")
    API_URL=$(gcloud run services describe raimy-api --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")
    MCP_URL=$(gcloud run services describe mcp-service --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")
    AGENT_URL=$(gcloud run services describe raimy-bot --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")

    # Update auth-service with API_URL
    if [ ! -z "$AUTH_URL" ]; then
        gcloud run services update auth-service \
            --region="${REGION}" \
            --set-env-vars "API_URL=${API_URL}" \
            --project="${PROJECT_ID}"
    fi

    # Update raimy-api with AUTH_SERVICE_URL and AGENT_SERVICE_URL
    if [ ! -z "$API_URL" ]; then
        gcloud run services update raimy-api \
            --region="${REGION}" \
            --set-env-vars "AUTH_SERVICE_URL=${AUTH_URL},AGENT_SERVICE_URL=${AGENT_URL}" \
            --project="${PROJECT_ID}"
    fi

    # Update mcp-service with API_URL and AUTH_SERVICE_URL
    if [ ! -z "$MCP_URL" ]; then
        gcloud run services update mcp-service \
            --region="${REGION}" \
            --set-env-vars "API_URL=${API_URL},AUTH_SERVICE_URL=${AUTH_URL}" \
            --project="${PROJECT_ID}"
    fi

    # Update raimy-bot with API_URL, AUTH_SERVICE_URL, and MCP_SERVER_URL
    if [ ! -z "$AGENT_URL" ]; then
        gcloud run services update raimy-bot \
            --region="${REGION}" \
            --set-env-vars "API_URL=${API_URL},AUTH_SERVICE_URL=${AUTH_URL},MCP_SERVER_URL=${MCP_URL}/mcp" \
            --project="${PROJECT_ID}"
    fi

    echo -e "${GREEN}✓ Service URLs updated!${NC}"
}

# Deploy services based on argument
case "${1:-all}" in
    "auth-service")
        deploy_service "auth-service" "../server/auth-service" "Dockerfile" "8001" "uvicorn,main:app,--host,0.0.0.0,--port,8001"
        ;;
    "raimy-api")
        deploy_service "raimy-api" ".." "Dockerfile" "8000" "uvicorn,server.app.main:app,--host,0.0.0.0,--port,8000"
        ;;
    "mcp-service")
        deploy_service "mcp-service" "../server" "mcp_service/Dockerfile" "8002" "python,mcp_service/server.py"
        ;;
    "raimy-bot")
        deploy_service "raimy-bot" "../server/agent-service" "Dockerfile" "8003" "uvicorn,main:app,--host,0.0.0.0,--port,8003"
        ;;
    "all")
        echo -e "${YELLOW}Deploying all services...${NC}"
        echo ""

        # Deploy in dependency order
        deploy_service "auth-service" "../server/auth-service" "Dockerfile" "8001" "uvicorn,main:app,--host,0.0.0.0,--port,8001"
        deploy_service "raimy-api" ".." "Dockerfile" "8000" "uvicorn,server.app.main:app,--host,0.0.0.0,--port,8000"
        deploy_service "mcp-service" "../server" "mcp_service/Dockerfile" "8002" "python,mcp_service/server.py"
        deploy_service "raimy-bot" "../server/agent-service" "Dockerfile" "8003" "uvicorn,main:app,--host,0.0.0.0,--port,8003"

        # Update service-to-service URLs after all services are deployed
        update_service_urls

        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}All services deployed successfully!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "Service URLs:"
        echo "  Auth Service:  $(gcloud run services describe auth-service --region=${REGION} --format='value(status.url)')"
        echo "  API Service:   $(gcloud run services describe raimy-api --region=${REGION} --format='value(status.url)')"
        echo "  MCP Service:   $(gcloud run services describe mcp-service --region=${REGION} --format='value(status.url)')"
        echo "  Agent Service: $(gcloud run services describe raimy-bot --region=${REGION} --format='value(status.url)')"
        echo ""
        echo "Next steps:"
        echo "1. Update your Vercel frontend env vars with the API URL"
        echo "2. Configure Google OAuth redirect URIs"
        ;;
    *)
        echo "Usage: ./deploy.sh [service-name|all]"
        echo "Services: auth-service, raimy-api, mcp-service, raimy-bot, all"
        exit 1
        ;;
esac