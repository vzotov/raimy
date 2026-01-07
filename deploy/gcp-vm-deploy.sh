#!/bin/bash

# GCP Compute Engine Deployment Script for Raimy
# Deploys all services to a single e2-micro VM (free tier)
#
# Prerequisites:
# 1. gcloud CLI installed and authenticated
# 2. GCP project created
# 3. .env.prod file configured

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
ZONE="us-east1-b"  # Free tier zone (East Coast)
INSTANCE_NAME="raimy-backend"
MACHINE_TYPE="e2-micro"  # Free tier: 0.6GB RAM, 2 vCPUs
DISK_SIZE="30GB"  # Free tier: 30GB standard persistent disk

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== GCP Compute Engine Deployment ===${NC}"
echo -e "${GREEN}Project: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Instance: ${INSTANCE_NAME}${NC}"
echo -e "${GREEN}Machine Type: ${MACHINE_TYPE} (Free Tier)${NC}"
echo ""

# Check if .env.prod exists
if [ ! -f "../.env.prod" ]; then
    echo -e "${RED}Error: .env.prod file not found!${NC}"
    echo "Please create .env.prod from .env.prod.example"
    exit 1
fi

# Function to create VM
create_vm() {
    echo -e "${YELLOW}Creating VM instance...${NC}"

    gcloud compute instances create "${INSTANCE_NAME}" \
        --project="${PROJECT_ID}" \
        --zone="${ZONE}" \
        --machine-type="${MACHINE_TYPE}" \
        --network-interface=network-tier=STANDARD,subnet=default \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --tags=http-server,https-server \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=${DISK_SIZE} \
        --boot-disk-type=pd-standard \
        --no-shielded-secure-boot \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --labels=app=raimy,env=production \
        --reservation-affinity=any

    echo -e "${GREEN}✓ VM instance created${NC}"
}

# Function to configure firewall
setup_firewall() {
    echo -e "${YELLOW}Setting up firewall rules...${NC}"

    # Allow HTTP
    gcloud compute firewall-rules create allow-http \
        --project="${PROJECT_ID}" \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:80 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=http-server \
        --quiet 2>/dev/null || echo "Firewall rule 'allow-http' already exists"

    # Allow HTTPS
    gcloud compute firewall-rules create allow-https \
        --project="${PROJECT_ID}" \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:443 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=https-server \
        --quiet 2>/dev/null || echo "Firewall rule 'allow-https' already exists"

    echo -e "${GREEN}✓ Firewall rules configured${NC}"
}

# Function to setup VM
setup_vm() {
    echo -e "${YELLOW}Setting up VM with Docker and services...${NC}"

    # Wait for VM to be ready and SSH to start
    echo -e "${YELLOW}Waiting for VM to boot and SSH to be ready...${NC}"
    sleep 30

    # Wait for SSH to be available
    for i in {1..12}; do
        if gcloud compute ssh "${INSTANCE_NAME}" \
            --zone="${ZONE}" \
            --project="${PROJECT_ID}" \
            --command="echo 'SSH ready'" 2>/dev/null; then
            echo -e "${GREEN}✓ SSH is ready${NC}"
            break
        fi
        echo "Waiting for SSH... attempt $i/12"
        sleep 10
    done

    # Copy setup script
    gcloud compute scp --zone="${ZONE}" \
        setup-vm.sh "${INSTANCE_NAME}":~/ \
        --project="${PROJECT_ID}"

    # Run setup script
    gcloud compute ssh "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --command="chmod +x ~/setup-vm.sh && ~/setup-vm.sh"

    echo -e "${GREEN}✓ VM setup completed${NC}"
}

# Function to deploy code
deploy_code() {
    echo -e "${YELLOW}Deploying application code...${NC}"

    # Create tarball of project (excluding node_modules, .git, etc.)
    cd ..
    tar --exclude='./client/node_modules' \
        --exclude='./client/.next' \
        --exclude='./.git' \
        --exclude='./venv' \
        --exclude='./__pycache__' \
        --exclude='*.pyc' \
        --exclude='./.env' \
        --exclude='./.env.*' \
        -czf /tmp/raimy-deploy.tar.gz .
    cd deploy

    # Copy to VM
    gcloud compute scp --zone="${ZONE}" \
        /tmp/raimy-deploy.tar.gz "${INSTANCE_NAME}":~/ \
        --project="${PROJECT_ID}"

    # Extract and start services
    echo -e "${YELLOW}Extracting code on VM...${NC}"
    gcloud compute ssh "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --command="
            mkdir -p ~/raimy
            tar -xzf ~/raimy-deploy.tar.gz -C ~/raimy
            echo 'Code extracted successfully'
        "

    # Copy .env.prod file to VM
    echo -e "${YELLOW}Configuring environment variables...${NC}"
    gcloud compute scp --zone="${ZONE}" \
        ../.env.prod "${INSTANCE_NAME}":~/raimy/.env \
        --project="${PROJECT_ID}"

    echo -e "${YELLOW}Building Docker images (this takes 5-10 minutes)...${NC}"
    gcloud compute ssh "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --command="
            cd ~/raimy
            echo 'Starting Docker build...'
            docker-compose -f docker-compose.prod.yml build --progress=plain
            echo 'Build complete, starting containers...'
            docker-compose -f docker-compose.prod.yml up -d
            echo 'Containers started'
        "

    # Clean up
    rm /tmp/raimy-deploy.tar.gz

    echo -e "${GREEN}✓ Application deployed${NC}"
}

# Function to get VM IP
get_vm_ip() {
    VM_IP=$(gcloud compute instances describe "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    echo "${VM_IP}"
}

# Main deployment flow
case "${1:-create}" in
    "create")
        echo -e "${YELLOW}Creating new deployment...${NC}"
        create_vm
        setup_firewall
        setup_vm
        deploy_code

        VM_IP=$(get_vm_ip)

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Deployment Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "VM IP Address: ${VM_IP}"
        echo "Backend accessible at: http://${VM_IP}/api"
        echo ""
        echo -e "${YELLOW}⚠ IMPORTANT: Complete OAuth and domain setup${NC}"
        echo ""
        echo "1. Update Google OAuth Console authorized redirect URIs:"
        echo "   Add: https://raimy.app/auth/google/callback"
        echo "   (Update with your actual domain)"
        echo ""
        echo "2. Configure Vercel environment variables:"
        echo "   API_URL=https://api.raimy.app"
        echo "   NEXT_PUBLIC_WS_HOST=api.raimy.app"
        echo ""
        echo "3. If you changed .env.prod, redeploy:"
        echo "   ./gcp-vm-deploy.sh update"
        echo ""
        echo "Useful commands:"
        echo "  SSH to VM:        gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE}"
        echo "  View logs:        ./gcp-vm-deploy.sh logs"
        echo "  Restart services: gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --command='cd ~/raimy && docker-compose -f docker-compose.prod.yml restart'"
        ;;

    "update")
        echo -e "${YELLOW}Updating existing deployment...${NC}"
        deploy_code

        VM_IP=$(get_vm_ip)

        echo ""
        echo -e "${GREEN}Update Complete!${NC}"
        echo "Backend accessible at: https://api.raimy.app"
        ;;

    "destroy")
        echo -e "${RED}Destroying VM instance...${NC}"
        read -p "Are you sure you want to delete ${INSTANCE_NAME}? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            gcloud compute instances delete "${INSTANCE_NAME}" \
                --zone="${ZONE}" \
                --project="${PROJECT_ID}" \
                --quiet
            echo -e "${GREEN}✓ VM instance deleted${NC}"
        else
            echo "Cancelled"
        fi
        ;;

    "ssh")
        gcloud compute ssh "${INSTANCE_NAME}" \
            --zone="${ZONE}" \
            --project="${PROJECT_ID}"
        ;;

    "logs")
        gcloud compute ssh "${INSTANCE_NAME}" \
            --zone="${ZONE}" \
            --project="${PROJECT_ID}" \
            --command="cd ~/raimy && docker-compose -f docker-compose.prod.yml logs -f"
        ;;

    "ip")
        VM_IP=$(get_vm_ip)
        echo "VM IP: ${VM_IP}"
        echo "Backend API: https://api.raimy.app"
        echo "Frontend: https://raimy.app"
        ;;

    *)
        echo "Usage: ./gcp-vm-deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  create   - Create new VM and deploy (default)"
        echo "  update   - Update code on existing VM"
        echo "  destroy  - Delete the VM instance"
        echo "  ssh      - SSH into the VM"
        echo "  logs     - View application logs"
        echo "  ip       - Show VM IP address"
        exit 1
        ;;
esac