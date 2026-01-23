# GCP Compute Engine Deployment

All-in-one deployment to GCP e2-micro VM (free tier). Everything runs on one VM: all services, PostgreSQL, Redis, and nginx.

## Quick Start

```bash
# 1. Use existing GCP project or create new one
# List existing projects: gcloud projects list
gcloud config set project YOUR_PROJECT_ID
gcloud services enable compute.googleapis.com

# 2. Configure environment
cp ../.env.prod.example ../.env.prod
# Edit .env.prod with your values

# 3. Authenticate
gcloud auth login
gcloud auth application-default login

# 4. Deploy
chmod +x gcp-vm-deploy.sh setup-vm.sh
./gcp-vm-deploy.sh create
```

## Commands

```bash
# Deploy new VM and all services
./gcp-vm-deploy.sh create

# Update code on existing VM
./gcp-vm-deploy.sh update

# SSH into VM
./gcp-vm-deploy.sh ssh

# View logs
./gcp-vm-deploy.sh logs

# Get VM IP address
./gcp-vm-deploy.sh ip

# Destroy VM
./gcp-vm-deploy.sh destroy
```

## After Deployment

1. Get your VM's IP: `./gcp-vm-deploy.sh ip`
2. Update Vercel: `NEXT_PUBLIC_API_URL=http://YOUR_VM_IP/api`
3. Update Google OAuth redirect URI: `http://YOUR_VM_IP/api/auth/google/callback`
4. Test: `curl http://YOUR_VM_IP/api/health`

## Architecture

**Single e2-micro VM (0.6GB RAM, 2 vCPUs, 30GB disk)**

```
Internet → nginx (port 80/443)
           ↓
           /api → raimy-api (8000)
                   ├─ auth-service (8001)
                   ├─ mcp-service (8002)
                   ├─ agent-service (8003)
                   ├─ PostgreSQL (5432)
                   └─ Redis (6379)
```

All services run via docker-compose on the VM.

## Common Operations

### View Service Status

```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml ps
```

### Restart Services

```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml restart
```

### Database Backup

```bash
./gcp-vm-deploy.sh ssh
docker-compose -f ~/raimy/docker-compose.prod.yml exec postgres \
  pg_dump -U raimy_user raimy > backup-$(date +%Y%m%d).sql
```

### Check Resource Usage

```bash
./gcp-vm-deploy.sh ssh
free -h           # Memory
df -h             # Disk
docker stats      # Container resources
```

## Cost

- **$0/month** (within GCP free tier)
- Free tier: 1 e2-micro instance in us-central1, us-west1, or us-east1
- If you exceed free tier, ~$6/month for e2-micro

## Troubleshooting

### Out of Memory

e2-micro has only 0.6GB RAM. If services crash:

```bash
# Check memory
./gcp-vm-deploy.sh ssh
free -h
docker stats

# Upgrade to e2-small (~$15/month, 2GB RAM)
gcloud compute instances stop raimy-backend --zone=us-central1-a
gcloud compute instances set-machine-type raimy-backend \
  --zone=us-central1-a --machine-type=e2-small
gcloud compute instances start raimy-backend --zone=us-central1-a
```

### Can't Access from Internet

```bash
# Check firewall
gcloud compute firewall-rules list

# Check nginx
./gcp-vm-deploy.sh ssh
sudo systemctl status nginx
curl http://localhost/api/health
```

## Files

- `gcp-vm-deploy.sh` - Main deployment script
- `setup-vm.sh` - VM initialization script (runs on VM)
- `../docker-compose.prod.yml` - Production docker-compose config
- `../.env.prod` - Production environment variables (not committed)
- `../DEPLOYMENT.md` - Full deployment guide
