import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Dict
import os
import subprocess
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn
import httpx

# Import routers
from .routes.timers import create_timers_router
from .routes.recipes import create_recipes_router
from .routes.debug import create_debug_router
from .routes.meal_planner_sessions import create_meal_planner_sessions_router
from core.auth_client import auth_client
from agents.auth_proxy import router as auth_proxy_router

# Global state for SSE connections
sse_connections: List[asyncio.Queue] = []


class ConnectionManager:
    """Manages WebSocket connections for chat sessions"""

    def __init__(self):
        # Map of session_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection for a session"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection for a session"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_message(self, session_id: str, message: dict):
        """Send message to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                self.disconnect(session_id)

    async def receive_message(self, session_id: str) -> dict:
        """Receive message from a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                return await websocket.receive_json()
            except Exception as e:
                logger.error(f"Error receiving message from session {session_id}: {e}")
                raise


# Global connection manager
connection_manager = ConnectionManager()


async def run_database_migrations():
    """Run database migrations on startup if enabled"""
    auto_migrate = os.getenv("AUTO_MIGRATE", "true").lower() == "true"

    if not auto_migrate:
        print("⚠️  AUTO_MIGRATE=false, skipping database migrations")
        print("💡 Run 'alembic upgrade head' manually if needed")
        return

    try:
        print("🔄 Running database migrations...")

        # Run alembic upgrade head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            check=True
        )

        print("✅ Database migrations completed successfully")
        if result.stdout:
            print(f"Migration output: {result.stdout}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Database migration failed: {e}")
        print(f"Migration error: {e.stderr}")

        # In production, you might want to fail fast
        # For development, we'll continue and let the developer handle it
        if os.getenv("FAIL_ON_MIGRATION_ERROR", "false").lower() == "true":
            raise RuntimeError("Database migration failed") from e
        else:
            print("⚠️  Continuing startup despite migration failure")
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        if os.getenv("FAIL_ON_MIGRATION_ERROR", "false").lower() == "true":
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting FastAPI server...")

    # Run database migrations on startup
    await run_database_migrations()

    print("✅ FastAPI server ready!")
    yield
    print("🛑 Shutting down FastAPI server...")


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
            "debug": "/debug/*",
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
        "websocket_connections": len(connection_manager.active_connections),
        "timestamp": asyncio.get_event_loop().time()
    }


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(None, description="JWT authentication token")
):
    """
    ## WebSocket Chat Endpoint

    Establishes WebSocket connection for real-time chat with the agent.

    Parameters:
    - `session_id`: The meal planner session ID
    - `token`: JWT authentication token (query parameter)

    Message format:
    - Client sends: `{"type": "user_message", "content": "text"}`
    - Server sends: `{"type": "agent_message", "content": "text"}`
    - Server sends: `{"type": "error", "message": "error text"}`
    """
    # TODO: Validate JWT token when auth is ready
    # For now, we'll accept connections without strict auth validation

    try:
        # Connect WebSocket
        await connection_manager.connect(session_id, websocket)

        # Send connection confirmation
        await connection_manager.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to chat"
        })

        # Get agent service URL from environment
        agent_url = os.getenv("AGENT_SERVICE_URL", "http://raimy-bot:8003")

        # Listen for messages from client
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_json()

            logger.info(f"Received message from session {session_id}: {data}")

            # Extract message content
            message_type = data.get("type")
            content = data.get("content")
            user_id = data.get("user_id", "anonymous")

            if message_type == "user_message" and content:
                try:
                    # Forward message to agent service
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            f"{agent_url}/agent/chat",
                            json={
                                "session_id": session_id,
                                "message": content,
                                "user_id": user_id
                            }
                        )

                        if response.status_code == 200:
                            agent_response = response.json()

                            # Send agent response back to client
                            await connection_manager.send_message(session_id, {
                                "type": "agent_message",
                                "content": agent_response.get("response"),
                                "message_id": agent_response.get("message_id")
                            })
                        else:
                            logger.error(f"Agent service error: {response.status_code}")
                            await connection_manager.send_message(session_id, {
                                "type": "error",
                                "message": "Failed to get response from agent"
                            })

                except httpx.RequestError as e:
                    logger.error(f"Failed to connect to agent service: {e}")
                    await connection_manager.send_message(session_id, {
                        "type": "error",
                        "message": "Agent service unavailable"
                    })
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await connection_manager.send_message(session_id, {
                        "type": "error",
                        "message": str(e)
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        connection_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        connection_manager.disconnect(session_id)


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
app.include_router(create_meal_planner_sessions_router(broadcast_event))
app.include_router(create_debug_router())
# Auth proxy router - forwards requests to auth microservice
app.include_router(auth_proxy_router)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
