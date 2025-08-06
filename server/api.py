import asyncio
import json
from contextlib import asynccontextmanager
from typing import List
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Import routers
from routes.timers import create_timers_router
from routes.recipes import create_recipes_router
from routes.auth import create_auth_router, oauth

# Global state for SSE connections
sse_connections: List[asyncio.Queue] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FastAPI server...")
    yield
    print("Shutting down FastAPI server...")


app = FastAPI(
    title="Raimy Cooking Assistant API",
    description="""
    ## 🍳 Raimy Cooking Assistant API
    
    A comprehensive API for managing cooking recipes, timers, and real-time cooking assistance.
    
    ### Features:
    * 🔐 **Authentication** - Google OAuth with JWT support
    * 📝 **Recipe Management** - Create, read, and manage cooking recipes
    * ⏰ **Timer System** - Set and manage cooking timers
    * 📡 **Real-time Events** - SSE for live updates
    * 👤 **User Management** - User-specific recipe storage
    
    ### Quick Start:
    1. **Authenticate** via `/auth/login`
    2. **Create recipes** with `/api/recipes`
    3. **Set timers** with `/api/timers/set`
    4. **Listen for events** at `/api/events`
    
    ### Authentication:
    - **Web Apps**: Use session-based auth (cookies)
    - **Mobile/API**: Use JWT tokens with `Authorization: Bearer <token>`
    """,
    version="1.0.0",
    contact={
        "name": "Raimy Team",
        "email": "support@raimy.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add SessionMiddleware for OAuth support
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SIGNER_SECRET", "supersecret")
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Google OAuth client with latest API
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Environment variable to control debug logging
if os.getenv("AUTH_DEBUG", "false").lower() == "true":
    logger.setLevel(logging.DEBUG)

logger.debug("Checking environment variables...")
logger.debug(f"All env vars: {[k for k in os.environ.keys() if 'GOOGLE' in k or 'OAUTH' in k or 'CLIENT' in k]}")

google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

logger.debug(f"GOOGLE_CLIENT_ID = {'SET' if google_client_id else 'NOT SET'}")
logger.debug(f"GOOGLE_CLIENT_SECRET = {'SET' if google_client_secret else 'NOT SET'}")

if not google_client_id or not google_client_secret:
    logger.warning("Google OAuth credentials not found!")
    logger.warning("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables")
    logger.warning("You can get these from: https://console.cloud.google.com/apis/credentials")
    logger.warning("For now, OAuth authentication will be disabled")
else:
    try:
        logger.debug(f"Attempting to register OAuth client with ID: {google_client_id[:10]}...")
        # Use manual OAuth configuration (no OpenID Connect discovery)
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            access_token_url="https://accounts.google.com/o/oauth2/token",
            access_token_params=None,
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            authorize_params=None,
            api_base_url="https://www.googleapis.com/oauth2/v1/",
            jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
            client_kwargs={
                "scope": "openid email profile",
                "token_endpoint_auth_method": "client_secret_post"
            },
        )
        logger.info("Google OAuth client registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Google OAuth client: {e}")
        logger.error("OAuth authentication will be disabled")


async def broadcast_event(event_type: str, data: dict):
    """Broadcast event to all connected SSE clients"""
    event_data = {"type": event_type, "data": data}

    # Remove disconnected clients
    disconnected = []
    for i, queue in enumerate(sse_connections):
        try:
            await queue.put(json.dumps(event_data))
        except Exception:
            disconnected.append(i)

    # Remove disconnected clients
    for i in reversed(disconnected):
        sse_connections.pop(i)


@app.get("/", tags=["Root"])
async def root():
    """
    ## API Root
    
    Welcome to the Raimy Cooking Assistant API!
    
    Returns basic API information and available endpoints.
    """
    return {
        "message": "Raimy Cooking Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/auth/*",
            "recipes": "/api/recipes/*",
            "timers": "/api/timers/*",
            "events": "/api/events",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    ## Health Check
    
    Check the health status of the API and get current SSE connection count.
    
    Returns:
    - `status`: API health status
    - `connections`: Number of active SSE connections
    """
    return {
        "status": "healthy", 
        "connections": len(sse_connections),
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/api/events", tags=["Events"])
async def events():
    """
    ## Server-Sent Events (SSE)
    
    Real-time event stream for cooking updates, timer notifications, and user events.
    
    ### Event Types:
    - `timer_set`: When a timer is started
    - `recipe_name`: When a recipe name is sent
    - `user_logout`: When a user logs out
    
    ### Usage:
    ```javascript
    const eventSource = new EventSource('/api/events');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.type, data.data);
    };
    ```
    """
    queue = asyncio.Queue()
    sse_connections.append(queue)

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"event": "message", "data": data}
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "ping", "data": "keepalive"}
        except Exception as e:
            print(f"SSE connection error: {e}")
        finally:
            if queue in sse_connections:
                sse_connections.remove(queue)

    return EventSourceResponse(event_generator())


# Include routers with injected broadcast function
app.include_router(create_timers_router(broadcast_event))
app.include_router(create_recipes_router(broadcast_event))
app.include_router(create_auth_router(broadcast_event))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
