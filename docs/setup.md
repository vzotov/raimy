# Deployment Setup Checklist

Follow these steps to deploy the backend to GCP for the first time.

## 1. Create Production Environment File

```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` and fill in these values:

```bash
# REQUIRED - Get from OpenAI
OPENAI_API_KEY=sk-...

# REQUIRED - Generate secure keys
SERVICE_API_KEY=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)

# REQUIRED - From Google OAuth (same as dev)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# REQUIRED - Create a secure password
POSTGRES_PASSWORD=your_secure_password_here

# REQUIRED - Your domains
API_DOMAIN=api.yourdomain.com
FRONTEND_DOMAIN=yourdomain.com
LETSENCRYPT_EMAIL=you@yourdomain.com

# OPTIONAL - LangSmith for debugging
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your_key
# LANGCHAIN_PROJECT=raimy-production
```

**Quick command to generate keys:**
```bash
echo "SERVICE_API_KEY=$(openssl rand -base64 32)"
echo "JWT_SECRET=$(openssl rand -base64 32)"
```

## 2. Set Up GCP Project

```bash
# List your projects and use existing one
gcloud projects list

# Set your project as active
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com

# Authenticate
gcloud auth login
gcloud auth application-default login
```

If you don't have a GCP project, create one at https://console.cloud.google.com/projectcreate

Enable billing at https://console.cloud.google.com/billing (required even for free tier).

## 3. Deploy to GCP

```bash
cd deploy

# Make scripts executable
chmod +x gcp-vm-deploy.sh setup-vm.sh

# Deploy everything (creates VM, installs Docker, starts all services)
./gcp-vm-deploy.sh create
```

Takes ~10-15 minutes. Save the VM IP shown at the end.

## 4. Point Your Domain

Point your `API_DOMAIN` DNS A record at the VM IP. Caddy will automatically obtain an SSL certificate once DNS propagates.

## 5. Update Vercel (Frontend)

1. Go to your Vercel project → Settings → Environment Variables
2. Set:
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   ```
3. Redeploy the frontend

## 6. Update Google OAuth

1. Go to https://console.developers.google.com/apis/credentials
2. Select your OAuth client
3. Add to "Authorized redirect URIs":
   ```
   https://api.yourdomain.com/auth/google/callback
   ```
4. Save

## 7. Test

```bash
# Get VM IP
cd deploy
./gcp-vm-deploy.sh ip

# Test API health
curl https://api.yourdomain.com/api/health
# Should return: {"status":"healthy"}
```

Then open the frontend, sign in with Google, and create a recipe.

---

## Common Commands

```bash
cd deploy

./gcp-vm-deploy.sh logs -f   # Follow logs
./gcp-vm-deploy.sh ssh        # SSH into VM
./gcp-vm-deploy.sh ip         # Get VM IP
```

## Troubleshooting

**Services won't start:**
```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

**Out of memory** (e2-micro has ~0.6GB RAM):
```bash
# Upgrade to e2-small (~$15/month, 2GB RAM)
gcloud compute instances stop raimy-backend --zone=us-east1-b
gcloud compute instances set-machine-type raimy-backend \
  --zone=us-east1-b --machine-type=e2-small
gcloud compute instances start raimy-backend --zone=us-east1-b
```

For full ops documentation see [deployment.md](deployment.md).
