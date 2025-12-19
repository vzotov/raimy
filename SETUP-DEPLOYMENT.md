# Deployment Setup Checklist

Follow these steps to deploy your backend to GCP.

## 1. Create Production Environment File

```bash
# Copy the example file
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

**Note:** If you don't have a GCP project yet, create one at https://console.cloud.google.com/projectcreate

**Enable billing:** Go to https://console.cloud.google.com/billing and link a billing account (required even for free tier).

## 3. Deploy to GCP

```bash
# Navigate to deploy directory
cd deploy

# Make scripts executable
chmod +x gcp-vm-deploy.sh setup-vm.sh

# Deploy everything
./gcp-vm-deploy.sh create
```

**This will take 10-15 minutes.** It will:
- Create a VM instance
- Install Docker and nginx
- Deploy all services
- Output your VM's IP address

**Save the IP address shown at the end!**

## 4. Update Vercel (Frontend)

1. Go to your Vercel project settings
2. Navigate to Environment Variables
3. Update or add:
   ```
   NEXT_PUBLIC_API_URL=http://YOUR_VM_IP/api
   ```
4. Redeploy your frontend

## 5. Update Google OAuth

1. Go to https://console.developers.google.com/apis/credentials
2. Select your OAuth client
3. Add to "Authorized redirect URIs":
   ```
   http://YOUR_VM_IP/api/auth/google/callback
   ```
4. Save changes

## 6. Test Your Deployment

```bash
# Get your VM IP
cd deploy
./gcp-vm-deploy.sh ip

# Test API health
curl http://YOUR_VM_IP/api/health

# Should return: {"status":"healthy"}
```

**Test full flow:**
1. Open your Vercel frontend URL
2. Sign in with Google
3. Create a recipe
4. Verify it saves and works

## Done! 🎉

Your backend is now running on GCP's free tier.

---

## Common Commands

```bash
# View logs
cd deploy
./gcp-vm-deploy.sh logs

# SSH into VM
./gcp-vm-deploy.sh ssh

# Update code after changes
./gcp-vm-deploy.sh update

# Stop VM (to save costs if needed)
gcloud compute instances stop raimy-backend --zone=us-central1-a

# Start VM
gcloud compute instances start raimy-backend --zone=us-central1-a
```

## Troubleshooting

**If services won't start:**
```bash
./gcp-vm-deploy.sh ssh
cd ~/raimy
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

**If out of memory (e2-micro only has 0.6GB):**
```bash
# Upgrade to e2-small (~$15/month, 2GB RAM)
gcloud compute instances stop raimy-backend --zone=us-central1-a
gcloud compute instances set-machine-type raimy-backend \
  --zone=us-central1-a --machine-type=e2-small
gcloud compute instances start raimy-backend --zone=us-central1-a
```

## Next Steps (Optional)

1. **Set up custom domain** - Point DNS to your VM IP
2. **Add HTTPS** - Use Let's Encrypt (see DEPLOYMENT.md)
3. **Set up backups** - Automated PostgreSQL backups (see DEPLOYMENT.md)
4. **Monitor costs** - Set up billing alerts at $5/month

---

For detailed documentation, see [DEPLOYMENT.md](DEPLOYMENT.md)