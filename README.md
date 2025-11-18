# Raimy Cooking Assistant

A conversational AI cooking assistant that guides users through recipes step-by-step using voice interaction and real-time communication.

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- LiveKit credentials
- Google OAuth credentials (for authentication)

## Quick Start

### 1. Environment Setup

Create a `.env` file in the root directory:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google OAuth (required for authentication)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Session and JWT Secrets (generate secure random strings for production)
SESSION_SIGNER_SECRET=your_session_signer_secret_here
JWT_SECRET=your_jwt_secret_here

# Debug logging (optional - set to "true" to see detailed auth logs)
AUTH_DEBUG=false
```

### 2. Run Services

#### Start Backend (Docker)
```bash
# Build and start API and bot
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The backend services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

#### Start Frontend (Next.js)
```bash
# Navigate to client directory
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at:
- **Client**: http://localhost:3000