# Raimy Cooking Assistant

A conversational AI cooking assistant that helps you create, save, and play through recipes with AI-powered guidance.

**🚀 Deployed at: [raimy.app](https://raimy.app)**

## Features

- **Recipe Creator**: Create recipes with AI assistance through a conversational interface
- **My Recipes**: Browse and manage your saved recipe collection
- **Kitchen**: Interactive recipe playback with step-by-step guidance
- **Real-time AI interactions** via WebSocket
- **Google OAuth authentication**

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Google OAuth credentials (for authentication)

## Quick Start

### 1. Environment Setup

Create a `.env` file in the root directory (see `.env.example` for all options):

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Service API Key for internal service authentication
SERVICE_API_KEY=your_service_api_key_here

# PostgreSQL Database
POSTGRES_DB=raimy
POSTGRES_USER=your_postgres_user_here
POSTGRES_PASSWORD=your_postgres_password_here

# Optional: LangSmith for debugging AI agents
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your_langsmith_api_key_here
# LANGCHAIN_PROJECT=raimy-agent
```

### 2. Run Services

#### Start Backend (Docker)
```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# Or start with pgadmin but exclude it from logs
docker-compose up --build --no-attach pgadmin
```

The backend services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

#### Start Frontend (Next.js)
```bash
# Navigate to client directory
cd client

# Install dependencies
bun install

# Start development server
bun dev
```

The frontend will be available at:
- **Client**: http://localhost:3000