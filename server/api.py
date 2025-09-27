import asyncio
import json
from contextlib import asynccontextmanager
from typing import List
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Import routers
from routes.timers import create_timers_router
from routes.recipes import create_recipes_router
from auth_client import auth_client
from auth_proxy import router as auth_proxy_router

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
    * 📝 **Recipe Management** - Create, read, and manage cooking recipes
    * ⏰ **Timer System** - Set and manage cooking timers
    * 📡 **Real-time Events** - SSE for live updates
    * 👤 **User Management** - User-specific recipe storage

    ### Quick Start:
    1. **Authenticate** via Auth Service (port 8001)
    2. **Create recipes** with `/api/recipes`
    3. **Set timers** with `/api/timers/set`
    4. **Listen for events** at `/api/events`

    ### Authentication:
    - **Auth Service**: Handled by dedicated microservice on port 8001
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

# Session middleware not needed - auth handled by microservice

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth handled by auth microservice
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
# Auth proxy router - forwards requests to auth microservice
app.include_router(auth_proxy_router)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
