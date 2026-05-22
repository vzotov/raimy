# Deploying Raimy to Google Cloud Platform

All backend services run on a single GCP Compute Engine e2-micro VM via Docker Compose. The frontend is hosted on Vercel.

## Architecture

**Backend (GCP VM — us-east1-b, e2-micro):**
- `raimy-api` — main FastAPI service
- `auth-service` — Google OAuth
- `agent-service` — LangGraph AI agents
- PostgreSQL database
- Redis pub/sub
- Caddy reverse proxy (automatic HTTPS via Let's Encrypt)

**Frontend:** Vercel (Next.js), pointed at the backend domain via `NEXT_PUBLIC_API_URL`.

**Cost:** $0/month within GCP free tier (1 e2-micro/month in eligible zones).

---

## First-Time Setup

### 1. Prerequisites

- `gcloud` CLI installed and authenticated
- GCP project with billing enabled and Compute Engine API enabled:
  ```bash
  gcloud services enable compute.googleapis.com
  ```
- A domain name pointed at the VM's IP (needed for Caddy HTTPS)

### 2. Configure environment

```bash
cp .env.prod.example .env.prod
```

Fill in all values (see `.env.prod.example` for the full list). Key variables:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `SERVICE_API_KEY` | Inter-service auth key — `openssl rand -base64 32` |
| `JWT_SECRET` | JWT signing key — `openssl rand -base64 32` |
| `POSTGRES_PASSWORD` | Database password |
| `API_DOMAIN` | Backend domain (e.g. `api.raimy.app`) |
| `FRONTEND_DOMAIN` | Frontend domain (e.g. `raimy.app`) |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt certificate notifications |

### 3. Create the VM

```bash
cd deploy
./gcp-vm-deploy.sh create
```

This creates the VM, installs Docker, and does the first deployment. Takes ~10-15 minutes.

### 4. Configure Google OAuth

Add the VM's domain to your Google OAuth app's authorized redirect URIs:
- `https://<API_DOMAIN>/auth/google/callback`

Get the IP if needed: `./gcp-vm-deploy.sh ip`

---

## Deploying Updates (Release Process)

1. Merge to `main` and tag the release
2. Run from your local machine:

```bash
cd deploy
./deploy-from-github.sh main
```

This SSHs into the VM, pulls the tagged code from GitHub, rebuilds Docker images, and restarts services. Migrations run automatically on API startup.

**Full rebuild (no Docker cache):**
```bash
./deploy-from-github.sh main no-cache
```

---

## Common Operations

```bash
cd deploy

./gcp-vm-deploy.sh logs -f     # Follow all service logs
./gcp-vm-deploy.sh ssh          # SSH into VM
./gcp-vm-deploy.sh ip           # Get VM IP
./gcp-vm-deploy.sh update       # Redeploy from local files (use deploy-from-github.sh instead)
./gcp-vm-deploy.sh destroy      # Tear down VM and all data
```

**View specific service logs (via SSH):**
```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml logs -f agent-service
```

**Restart a service:**
```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml restart raimy-api
```

---

## Database Operations

```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy

# Access PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U raimy_user -d raimy

# Backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U raimy_user raimy > backup.sql

# Restore
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T postgres psql -U raimy_user -d raimy
```

---

## Troubleshooting

**Services not starting:**
```bash
./gcp-vm-deploy.sh logs
```

**Out of memory** (e2-micro has ~0.6GB RAM):
```bash
./gcp-vm-deploy.sh ssh
free -h
docker stats
```
Redis is capped at 128MB. If still tight, upgrade to e2-small (~$15/month, 2GB RAM).

**Check migration status:**
```bash
./gcp-vm-deploy.sh ssh
docker logs $(docker ps -q -f name=raimy-api) 2>&1 | grep -E '(migration|alembic|✅|❌)' | tail -10
```

**Disk full:**
```bash
./gcp-vm-deploy.sh ssh
df -h
docker system prune -a
```

---

## Upgrading the VM

```bash
# Stop VM
gcloud compute instances stop raimy-backend --zone=us-east1-b

# Change machine type
gcloud compute instances set-machine-type raimy-backend \
  --zone=us-east1-b \
  --machine-type=e2-small

# Start VM
gcloud compute instances start raimy-backend --zone=us-east1-b
```
