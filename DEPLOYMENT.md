# Deploying Raimy to Google Cloud Platform (Compute Engine)

This guide walks you through deploying all backend services to a single GCP Compute Engine e2-micro VM (free tier).

## Architecture Overview

**Single GCP VM (e2-micro) runs:**
- All 4 FastAPI services (raimy-api, auth-service, mcp-service, raimy-bot)
- PostgreSQL database
- Redis
- Nginx reverse proxy

**Cost:** $0/month (within free tier)

**Resources:**
- 0.6GB RAM (shared across all services)
- 2 vCPUs
- 30GB standard persistent disk

## Prerequisites

1. **GCP Account** with billing enabled (required for free tier)
2. **gcloud CLI** installed and authenticated
3. **Git** (to clone/pull code)

## Step 1: Configure GCP

### 1.1 Set Up GCP Project

You can use an existing GCP project or create a new one.

**Option A: Use existing project**
```bash
# List your projects
gcloud projects list

# Set your existing project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
```

**Option B: Create new project (optional)**
```bash
# Create a new project
gcloud projects create raimy-production --name="Raimy Production"

# Set as active project
gcloud config set project raimy-production

# Enable required APIs
gcloud services enable compute.googleapis.com
```

### 1.2 Set Up Billing

Even for free tier, billing must be enabled:
- Go to https://console.cloud.google.com/billing
- Link a billing account to your project
- Free tier: 1 e2-micro instance/month = $0

## Step 2: Configure Environment Variables

### 2.1 Create Production Environment File

```bash
# Copy the example file
cp .env.prod.example .env.prod

# Edit with your values
nano .env.prod  # or use your preferred editor
```

Fill in:
- `OPENAI_API_KEY` (your OpenAI key)
- `SERVICE_API_KEY` (generate: `openssl rand -base64 32`)
- `JWT_SECRET` (generate: `openssl rand -base64 32`)
- `GOOGLE_CLIENT_ID` (same as dev)
- `GOOGLE_CLIENT_SECRET` (same as dev)
- `POSTGRES_PASSWORD` (create a secure password)

### 2.2 Google OAuth Configuration

You'll update this after deployment with your VM's IP address.

## Step 3: Deploy to GCP

### 3.1 Authenticate gcloud

```bash
# Login to gcloud
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

### 3.2 Deploy Everything

```bash
# Navigate to deploy directory
cd deploy

# Make scripts executable
chmod +x gcp-vm-deploy.sh setup-vm.sh

# Deploy (creates VM, installs Docker, deploys services)
./gcp-vm-deploy.sh create
```

**This will:**
1. Create e2-micro VM instance in us-central1-a
2. Configure firewall rules (HTTP/HTTPS)
3. Install Docker and Docker Compose on VM
4. Set up nginx reverse proxy
5. Deploy all services via docker-compose
6. Start everything automatically

**Expected deploy time:** 10-15 minutes

**Output will show:**
```
VM IP Address: X.X.X.X
API Endpoint: http://X.X.X.X/api
API Docs: http://X.X.X.X/api/docs
```

## Step 4: Update Frontend (Vercel)

Update your Vercel environment variables:

1. Go to your Vercel project settings
2. Update `NEXT_PUBLIC_API_URL`:
   ```
   NEXT_PUBLIC_API_URL=http://YOUR_VM_IP/api
   ```
3. Redeploy frontend

## Step 5: Update Google OAuth

Add your VM's public IP to Google OAuth allowed redirect URIs:

1. Go to https://console.developers.google.com/apis/credentials
2. Edit your OAuth client
3. Add redirect URI:
   ```
   http://YOUR_VM_IP/api/auth/google/callback
   ```

## Step 6: Verify Deployment

### 6.1 Check Health

```bash
# Get VM IP
./gcp-vm-deploy.sh ip

# Test API health
curl http://YOUR_VM_IP/api/health

# Test API docs
open http://YOUR_VM_IP/api/docs
```

### 6.2 Check Logs

```bash
# View all service logs
./gcp-vm-deploy.sh logs

# SSH into VM
./gcp-vm-deploy.sh ssh

# Inside VM, check individual services
docker-compose -f ~/raimy/docker-compose.prod.yml ps
docker-compose -f ~/raimy/docker-compose.prod.yml logs raimy-api
docker-compose -f ~/raimy/docker-compose.prod.yml logs postgres
```

### 6.3 Test the Application

1. Open your Vercel frontend URL
2. Sign in with Google
3. Create a recipe
4. Verify it works end-to-end

## Common Operations

### Update Application Code

After code changes:

```bash
cd deploy
./gcp-vm-deploy.sh update
```

This rebuilds and restarts all services with new code.

### View Logs

```bash
# Follow all logs
./gcp-vm-deploy.sh logs

# Or SSH and view specific service
./gcp-vm-deploy.sh ssh
# Then:
cd ~/raimy
docker-compose -f docker-compose.prod.yml logs -f raimy-api
```

### Restart Services

```bash
# SSH into VM
./gcp-vm-deploy.sh ssh

# Restart all services
cd ~/raimy
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart raimy-api
```

### Stop/Start Services

```bash
# SSH into VM
./gcp-vm-deploy.sh ssh

# Stop all services
cd ~/raimy
docker-compose -f docker-compose.prod.yml stop

# Start all services
docker-compose -f docker-compose.prod.yml start

# Or down/up to recreate containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Database Operations

```bash
# SSH into VM
./gcp-vm-deploy.sh ssh

# Access PostgreSQL
docker-compose -f ~/raimy/docker-compose.prod.yml exec postgres psql -U raimy_user -d raimy

# Backup database
docker-compose -f ~/raimy/docker-compose.prod.yml exec postgres pg_dump -U raimy_user raimy > backup.sql

# Restore database
cat backup.sql | docker-compose -f ~/raimy/docker-compose.prod.yml exec -T postgres psql -U raimy_user -d raimy
```

### Check Resource Usage

```bash
# SSH into VM
./gcp-vm-deploy.sh ssh

# Check memory usage
free -h

# Check disk usage
df -h

# Check Docker container resources
docker stats
```

## Cost Management

### Free Tier Limits

**Compute Engine e2-micro:**
- 1 instance per month (us-west1, us-central1, us-east1)
- 30GB standard persistent disk
- 1GB snapshot storage

**With <100 requests/day:**
- Monthly cost: **$0** (within free tier)

### Monitor Costs

```bash
# View current billing
gcloud billing accounts list
gcloud billing projects describe raimy-production

# Set up budget alerts
# Go to: https://console.cloud.google.com/billing/budgets
# Create alert for $5/month to catch any overages
```

### Stop VM to Save Costs (Optional)

If you need to pause the service:

```bash
# Stop VM (stops billing for compute, keeps disk)
gcloud compute instances stop raimy-backend --zone=us-central1-a

# Start VM later
gcloud compute instances start raimy-backend --zone=us-central1-a
```

## Upgrading Resources

If you outgrow the free tier:

### Upgrade to Larger VM

```bash
# Stop VM
gcloud compute instances stop raimy-backend --zone=us-central1-a

# Change machine type
gcloud compute instances set-machine-type raimy-backend \
  --zone=us-central1-a \
  --machine-type=e2-small  # ~$15/month, 2GB RAM

# Start VM
gcloud compute instances start raimy-backend --zone=us-central1-a
```

### Add More Disk Space

```bash
# Resize disk to 50GB
gcloud compute disks resize raimy-backend \
  --size=50GB \
  --zone=us-central1-a

# SSH and resize filesystem
./gcp-vm-deploy.sh ssh
sudo resize2fs /dev/sda1
```

## Security Hardening (Recommended)

### Set Up HTTPS with Let's Encrypt

```bash
# SSH into VM
./gcp-vm-deploy.sh ssh

# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is set up automatically
```

### Restrict Firewall

```bash
# Remove public access to individual service ports
# (only expose nginx on 80/443)
gcloud compute firewall-rules create block-backend-ports \
  --direction=INGRESS \
  --priority=999 \
  --network=default \
  --action=DENY \
  --rules=tcp:8000,tcp:8001,tcp:8002,tcp:8003 \
  --source-ranges=0.0.0.0/0
```

### Enable Automated Backups

```bash
# SSH into VM
./gcp-vm-deploy.sh ssh

# Set up daily PostgreSQL backups
cat > ~/backup-db.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
docker-compose -f ~/raimy/docker-compose.prod.yml exec -T postgres pg_dump -U raimy_user raimy | gzip > ~/backups/raimy-$DATE.sql.gz
# Keep last 7 days
find ~/backups -name "raimy-*.sql.gz" -mtime +7 -delete
EOF

chmod +x ~/backup-db.sh
mkdir -p ~/backups

# Add to crontab (daily at 2am)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup-db.sh") | crontab -
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
./gcp-vm-deploy.sh logs

# Or SSH and check specific service
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs [service-name]
```

### Out of Memory

e2-micro only has 0.6GB RAM. If services crash:

```bash
# Check memory
./gcp-vm-deploy.sh ssh
free -h
docker stats

# Reduce Redis memory limit (in docker-compose.prod.yml)
# Already set to: --maxmemory 128mb

# Or upgrade to e2-small (~$15/month, 2GB RAM)
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
./gcp-vm-deploy.sh ssh
docker-compose -f ~/raimy/docker-compose.prod.yml ps postgres

# Check logs
docker-compose -f ~/raimy/docker-compose.prod.yml logs postgres

# Verify credentials in .env match services
cat ~/raimy/.env | grep POSTGRES
```

### Can't Access from Internet

```bash
# Check firewall rules
gcloud compute firewall-rules list

# Check nginx is running
./gcp-vm-deploy.sh ssh
sudo systemctl status nginx

# Test locally on VM
curl http://localhost/api/health
```

### Disk Full

```bash
# Check disk usage
./gcp-vm-deploy.sh ssh
df -h

# Clean up Docker
docker system prune -a

# Clean up logs
sudo journalctl --vacuum-time=3d

# Or resize disk (see "Upgrading Resources")
```

## Destroying the Deployment

To completely remove everything:

```bash
# Delete VM instance
cd deploy
./gcp-vm-deploy.sh destroy

# This will also delete:
# - All containers
# - PostgreSQL data
# - All logs

# Firewall rules remain (delete manually if needed):
gcloud compute firewall-rules delete allow-http
gcloud compute firewall-rules delete allow-https
```

## Next Steps

Once deployed and stable:

1. **Set up custom domain** - Configure DNS and add SSL with Let's Encrypt
2. **Enable automated backups** - Use the backup script in Security section
3. **Set up monitoring** - GCP Cloud Monitoring or external service
4. **Create staging environment** - Deploy another VM for testing
5. **Implement CI/CD** - Auto-deploy on git push

## Resources

- [Compute Engine Documentation](https://cloud.google.com/compute/docs)
- [GCP Free Tier](https://cloud.google.com/free)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)