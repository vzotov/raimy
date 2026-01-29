import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Dict
import os
import subprocess
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

# Import routers
from .routes.timers import create_timers_router
from .routes.recipes import create_recipes_router
from .routes.chat_sessions import create_chat_sessions_router
from .routes.config import router as config_router
from core.auth_client import auth_client
from core.redis_client import get_redis_client
from .routes.auth_proxy import router as auth_proxy_router
from .services import database_service


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
        logger.info(f"🔍 send_message called for session {session_id}")
        logger.info(f"🔍 Message type: {message.get('type')}, content type: {message.get('content', {}).get('type')}")

        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            logger.info(f"✅ Found active WebSocket connection for session {session_id}")
            try:
                await websocket.send_json(message)
                logger.info(f"📤 Successfully sent WebSocket message to session {session_id}")
            except Exception as e:
                logger.error(f"❌ Error sending message to session {session_id}: {e}")
                self.disconnect(session_id)
        else:
            logger.warning(f"⚠️  No active WebSocket connection found for session {session_id}")
            logger.warning(f"⚠️  Active sessions: {list(self.active_connections.keys())}")

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
import sys

# Configure logging
logging.basicConfig(
    format='%(levelname)s:     %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

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
            "chat": "/ws/chat/{session_id}",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    ## Health Check

    Check the health status of the API and get current WebSocket connection count.

    Returns:
    - `status`: API health status
    - `websocket_connections`: Number of active WebSocket connections
    """
    return {
        "status": "healthy",
        "websocket_connections": len(connection_manager.active_connections),
        "timestamp": asyncio.get_event_loop().time()
    }


async def get_websocket_user(websocket: WebSocket) -> dict:
    """
    Authenticate WebSocket connection using cookies

    Returns:
        User data dict if authenticated

    Raises:
        HTTPException if not authenticated
    """
    try:
        # Get cookies from WebSocket headers
        cookies = websocket.cookies

        # Create a fake request object with cookies for auth_client
        from starlette.requests import Request
        from starlette.datastructures import Headers

        # Build headers with cookies
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        headers = Headers({"cookie": cookie_header} if cookie_header else {})

        # Create minimal request for auth verification
        scope = {
            "type": "http",
            "headers": [(b"cookie", cookie_header.encode())],
        }
        request = Request(scope)

        # Verify authentication using existing auth_client
        auth_data = await auth_client.verify_auth(request)

        if not auth_data.get("authenticated"):
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = auth_data.get("user", {})

        # Store/update user data in database
        if user_data and user_data.get('email'):
            try:
                await database_service.save_user(user_data)
                logger.debug(f"WebSocket auth: Updated user data for {user_data.get('email')}")
            except Exception as e:
                logger.warning(f"Failed to store user data: {str(e)}")

        return user_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    ## WebSocket Chat Endpoint

    Establishes WebSocket connection for real-time chat with the agent.
    Authentication is done via session cookies.

    Parameters:
    - `session_id`: The chat session ID

    Message format:
    - Client sends: `{"type": "user_message", "content": {"type": "text", "content": "..."}}`
    - Server sends: `{"type": "agent_message", "content": {"type": "text", "content": "..."}}`
    - Server sends: `{"type": "system", "system_type": "connected|error", "message": "..."}`
    """
    # Authenticate user before accepting connection
    try:
        user = await get_websocket_user(websocket)
        logger.info(f"WebSocket authenticated for user: {user.get('email')}")
    except HTTPException as e:
        logger.warning(f"WebSocket auth failed: {e.detail}")
        await websocket.close(code=1008, reason="Authentication required")
        return
    except Exception as e:
        logger.error(f"WebSocket auth error: {str(e)}")
        await websocket.close(code=1011, reason="Authentication error")
        return

    # Initialize Redis client
    redis_client = get_redis_client()
    redis_task = None

    try:
        # Connect WebSocket
        await connection_manager.connect(session_id, websocket)

        # Send connection confirmation
        await connection_manager.send_message(session_id, {
            "type": "system",
            "content": {
                "type": "connected",
                "message": "Connected to chat"
            },
            "session_id": session_id
        })

        # Subscribe to Redis for this session
        async def redis_listener():
            """Background task to listen for Redis messages and forward to WebSocket"""
            try:
                async for message in redis_client.subscribe(f"session:{session_id}"):
                    # Extract message type and content
                    msg_type = message.get("type")
                    content = message.get("content", {})
                    content_type = content.get("type") if isinstance(content, dict) else None

                    logger.info(f"🔍 Redis message: type={msg_type}, content_type={content_type}")

                    # Route message to appropriate handler based on content type
                    if msg_type == "agent_message" and content_type:
                        match content_type:
                            # action from Kitchen agent
                            case "ingredients":
                                await handle_ingredients_message(content)

                            case "recipe_update":
                                await handle_recipe_update_message(content)

                            case "session_name":
                                await handle_session_name_message(content)

                            case _:
                                # timer, text - UI only, just forward
                                logger.info(f"{msg_type} passed through")
                                pass

                    # Always forward message to WebSocket for UI
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.warning(f"Failed to send WebSocket message (connection may be closed): {e}")

            except Exception as e:
                logger.error(f"Redis listener error: {e}", exc_info=True)

        async def handle_ingredients_message(content: dict):
            """Handle ingredients message - save to session.ingredients"""
            action = content.get("action", "set")
            items = content.get("items", [])
            logger.info(f"🥘 Ingredients: action={action}, count={len(items)}")

            await database_service.save_or_update_ingredients(
                session_id=session_id,
                ingredients=items,
                action=action
            )

        async def handle_recipe_update_message(content: dict):
            """Handle recipe_update message - save to session.recipe or Recipe table"""
            action = content.get("action")
            logger.info(f"📝 Recipe update: action={action}")

            match action:
                case "save_recipe":
                    # Immediate save to Recipe table (no debouncing)
                    try:
                        logger.info(f"💾 Saving recipe to Recipe table")
                        result = await database_service.save_recipe_from_session_data(session_id)

                        # Send success message
                        await websocket.send_json({
                            "type": "system",
                            "content": {
                                "type": "recipe_saved",
                                "recipe_id": result["recipe_id"],
                                "message": f"Recipe '{result['recipe']['name']}' saved successfully!"
                            }
                        })
                        logger.info(f"✅ Recipe saved: {result['recipe_id']}")
                    except Exception as e:
                        logger.error(f"❌ Failed to save recipe: {e}")
                        try:
                            await websocket.send_json({
                                "type": "system",
                                "content": {
                                    "type": "error",
                                    "message": f"Failed to save recipe: {str(e)}"
                                }
                            })
                        except:
                            pass  # WebSocket might be disconnected

                case "set_metadata":
                    # Save to session.recipe immediately
                    await database_service.save_or_update_recipe(
                        session_id=session_id,
                        action="set_metadata",
                        name=content.get("name"),
                        description=content.get("description"),
                        difficulty=content.get("difficulty"),
                        total_time_minutes=content.get("total_time_minutes"),
                        servings=content.get("servings"),
                        tags=content.get("tags"),
                    )

                case "set_ingredients":
                    # Save to session.recipe immediately
                    await database_service.save_or_update_recipe(
                        session_id=session_id,
                        action="set_ingredients",
                        ingredients=content.get("ingredients", [])
                    )

                case "set_steps":
                    # Save to session.recipe immediately
                    await database_service.save_or_update_recipe(
                        session_id=session_id,
                        action="set_steps",
                        steps=content.get("steps", [])
                    )

                case "set_nutrition":
                    # Save to session.recipe immediately
                    await database_service.save_or_update_recipe(
                        session_id=session_id,
                        action="set_nutrition",
                        nutrition=content.get("nutrition", {})
                    )

        async def handle_session_name_message(content: dict):
            """Handle session_name message - save to session.session_name"""
            session_name = content.get("name")
            if session_name:
                logger.info(f"📝 Session name: {session_name}")
                await database_service.update_session_name(
                    session_id=session_id,
                    session_name=session_name
                )

        # Start Redis listener as background task
        redis_task = asyncio.create_task(redis_listener())

        # Get agent service URL from environment
        agent_url = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8003")

        # Track if greeting has been sent (to avoid duplicates on reconnect)
        greeting_sent = False

        # Helper function to send greeting for new sessions
        async def send_greeting_if_needed():
            nonlocal greeting_sent
            if greeting_sent:
                return

            session_data = await database_service.get_chat_session(session_id)
            if not session_data:
                return

            messages = session_data.get("messages", [])
            session_type = session_data.get("session_type", "recipe-creator")

            # Only send greeting if session has no messages
            if len(messages) > 0:
                greeting_sent = True  # Already has messages, no greeting needed
                return

            # Get recipe name if available (for kitchen sessions with pre-loaded recipe)
            recipe_name = None
            recipe_id = session_data.get("recipe_id")
            if recipe_id and session_type == "kitchen":
                logger.info(f"🍳 Kitchen session with recipe_id={recipe_id}")
                recipe_data = await database_service.get_recipe_by_id(recipe_id)
                if recipe_data:
                    recipe_name = recipe_data.get("name")
                    logger.info(f"✅ Loaded recipe: {recipe_name}")
                else:
                    logger.warning(f"⚠️  Recipe {recipe_id} not found")

            # Call agent service for LLM-generated greeting
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{agent_url}/agent/greeting",
                        json={
                            "session_type": session_type,
                            "recipe_name": recipe_name,
                        },
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    greeting = response.json().get("greeting", "Hello! I'm Raimy.")
            except Exception as e:
                logger.error(f"Failed to get greeting from agent service: {e}")
                # Fallback greeting if agent service fails
                greeting = "Hi! I'm Raimy. What would you like to cook today?"

            # Save greeting to database (as structured TextContent)
            try:
                await database_service.add_message_to_session(
                    session_id=session_id,
                    role="assistant",
                    content={"type": "text", "content": greeting}
                )
            except Exception as e:
                logger.error(f"Failed to save greeting to database: {e}")

            # Send greeting as agent message
            await connection_manager.send_message(session_id, {
                "type": "agent_message",
                "content": {
                    "type": "text",
                    "content": greeting
                },
                "message_id": f"greeting-{session_id}"
            })

            greeting_sent = True
            logger.info(f"✅ Sent greeting for session {session_id}")

        # Listen for messages from client
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_json()

            logger.info(f"Received message from session {session_id}: {data}")

            # Extract message content
            message_type = data.get("type")
            content = data.get("content")

            # Handle client_ready signal - send greeting after frontend confirms it's ready
            if message_type == "client_ready":
                logger.info(f"📡 Client ready signal received for session {session_id}")
                await send_greeting_if_needed()
                continue

            if message_type == "user_message" and content:
                try:
                    # Extract text from MessageContent structure
                    # content = {type: 'text', content: 'actual message'}
                    message_text = content.get("content") if isinstance(content, dict) else content

                    # Send "thinking" status immediately for UI responsiveness
                    await connection_manager.send_message(session_id, {
                        "type": "system",
                        "content": {
                            "type": "thinking",
                            "message": "thinking"
                        }
                    })

                    # Forward message to agent service
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            f"{agent_url}/agent/chat",
                            json={
                                "session_id": session_id,
                                "message": message_text
                            }
                        )

                        if response.status_code != 200:
                            logger.error(f"Agent service error: {response.status_code}")
                            await connection_manager.send_message(session_id, {
                                "type": "system",
                                "content": {
                                    "type": "error",
                                    "message": "Failed to get response from agent"
                                }
                            })

                except httpx.RequestError as e:
                    logger.error(f"Failed to connect to agent service: {e}")
                    await connection_manager.send_message(session_id, {
                        "type": "system",
                        "content": {
                            "type": "error",
                            "message": "Agent service unavailable"
                        }
                    })
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await connection_manager.send_message(session_id, {
                        "type": "system",
                        "content": {
                            "type": "error",
                            "message": str(e)
                        }
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        connection_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        connection_manager.disconnect(session_id)
    finally:
        # Cancel Redis listener task
        if redis_task:
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass



# Include routers (no longer need broadcast_event injection)
app.include_router(create_timers_router(None))
app.include_router(create_recipes_router(None))
app.include_router(create_chat_sessions_router(None))
app.include_router(config_router)
# Auth proxy router - forwards requests to auth microservice
app.include_router(auth_proxy_router)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
