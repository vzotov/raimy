# Raimy Cooking Assistant

A conversational AI cooking assistant that guides users through recipes step-by-step using voice interaction and real-time communication.

## Features

- **Voice Interaction**: Real-time voice communication with the AI assistant
- **Step-by-step Guidance**: Patient, knowledgeable chef-like assistance
- **Timer Management**: Automatic timer setting for cooking steps
- **Real-time Updates**: Server-Sent Events (SSE) for live communication
- **Recipe Tracking**: Session management and recipe saving
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Architecture

- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Backend**: FastAPI with SSE for real-time communication
- **AI**: LiveKit Agents with OpenAI integration
- **Voice**: Silero VAD for voice activity detection
- **Containerization**: Docker for unified deployment

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- LiveKit credentials (optional for full voice features)

## Quick Start

### 1. Environment Setup

Create a `.env` file in the root directory:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# LiveKit (optional)
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

### 2. Run Services with Docker

```bash
# Build and start API and bot
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Bot**: Running in container

### 3. Development Mode

#### Start Services (Docker)
```bash
# Start API and bot in Docker
docker-compose up -d
```

#### Start Client (Next.js)
```bash
cd client
npm install
npm run dev
```

The client will be available at:
- **Client**: http://localhost:3000

## API Endpoints

### Core Endpoints
- `GET /` - API health check
- `GET /health` - Detailed health status
- `GET /api/events` - SSE endpoint for real-time events

### Recipe Management
- `POST /api/recipes/start` - Start a new cooking session
- `POST /api/recipes/save` - Save completed recipe
- `GET /api/sessions` - Get active sessions

### Timer Management
- `POST /api/timers/set` - Set a cooking timer

### Agent Control
- `POST /api/agent/start` - Start the LiveKit agent

## Real-time Events

The application uses Server-Sent Events (SSE) for real-time communication:

### Event Types
- `session_started` - New cooking session started
- `timer_set` - Timer has been set
- `recipe_completed` - Recipe session completed
- `ping` - Keepalive ping

### Example Event
```json
{
  "type": "timer_set",
  "data": {
    "duration": 240,
    "label": "to flip the steak",
    "started_at": 1234567890.123
  }
}
```

## Client Integration

Use the `useSSE` hook in your React components:

```typescript
import { useSSE } from '@/hooks/useSSE';

const MyComponent = () => {
  const { isConnected, lastEvent, sendEvent } = useSSE({
    onMessage: (event) => {
      console.log('Received event:', event);
    },
  });

  const handleStartRecipe = async () => {
    await sendEvent('recipes/start', {
      name: 'Grilled Steak',
      instructions: ['Preheat grill', 'Season steak', 'Cook 4 minutes per side']
    });
  };

  return (
    <div>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <button onClick={handleStartRecipe}>Start Recipe</button>
    </div>
  );
};
```

## Docker Commands

```bash
# Build the image
docker build -t raimy .

# Run the container
docker run -p 8000:8000 -p 3000:3000 raimy

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build --force-recreate
```

## Development

### Project Structure
```
raimy/
├── client/                 # Next.js frontend
│   ├── src/
│   │   ├── hooks/         # React hooks (including useSSE)
│   │   └── components/    # React components
│   └── package.json
├── server/                # FastAPI backend
│   ├── api.py            # FastAPI application
│   ├── main.py           # LiveKit agent
│   ├── prompts.py        # AI prompts
│   └── requirements.txt
├── Dockerfile            # Multi-stage Docker build
├── docker-compose.yml    # Docker Compose configuration
└── README.md
```

### Adding New Features

1. **New API Endpoints**: Add to `server/api.py`
2. **New Events**: Update the SSE broadcast in `server/api.py`
3. **New Tools**: Add to the agent tools in `server/main.py`
4. **UI Components**: Add to `client/src/components/`

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000 and 3000 are available
2. **Environment variables**: Check that all required env vars are set
3. **Docker build issues**: Clear Docker cache with `docker system prune`
4. **SSE connection issues**: Check CORS settings and network connectivity

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs raimy

# Follow logs in real-time
docker-compose logs -f
```