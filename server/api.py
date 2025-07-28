import asyncio
import json
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import uvicorn

from main import entrypoint
from livekit.agents import JobContext


# Data models
class RecipeRequest(BaseModel):
    name: str
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None


class TimerRequest(BaseModel):
    duration: int
    label: str


class RecipeSession(BaseModel):
    recipe_name: str
    steps: List[str]
    current_step: int
    timers: List[Dict]
    completed: bool = False


# Global state for SSE connections and active sessions
sse_connections: List[asyncio.Queue] = []
active_sessions: Dict[str, RecipeSession] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FastAPI server...")
    yield
    # Shutdown
    print("Shutting down FastAPI server...")


app = FastAPI(
    title="Raimy Cooking Assistant API",
    description="API for the Raimy cooking assistant with real-time SSE communication",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def broadcast_event(event_type: str, data: dict):
    """Broadcast event to all connected SSE clients"""
    event_data = {
        "type": event_type,
        "data": data
    }
    
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


@app.get("/")
async def root():
    return {"message": "Raimy Cooking Assistant API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(sse_connections)}


@app.post("/api/recipes/start")
async def start_recipe(recipe: RecipeRequest, background_tasks: BackgroundTasks):
    """Start a new cooking session"""
    session_id = f"session_{len(active_sessions) + 1}"
    
    session = RecipeSession(
        recipe_name=recipe.name,
        steps=recipe.instructions or [],
        current_step=0,
        timers=[]
    )
    
    active_sessions[session_id] = session
    
    # Broadcast session start
    await broadcast_event("session_started", {
        "session_id": session_id,
        "recipe_name": recipe.name
    })
    
    return {"session_id": session_id, "recipe_name": recipe.name}


@app.post("/api/timers/set")
async def set_timer(timer: TimerRequest):
    """Set a timer for the current cooking step"""
    timer_data = {
        "duration": timer.duration,
        "label": timer.label,
        "started_at": asyncio.get_event_loop().time()
    }
    
    # Broadcast timer set event
    await broadcast_event("timer_set", timer_data)
    
    return {"message": f"Timer set for {timer.duration} seconds: {timer.label}"}


@app.post("/api/recipes/save")
async def save_recipe(recipe_data: dict):
    """Save completed recipe session"""
    # Broadcast recipe completion
    await broadcast_event("recipe_completed", recipe_data)
    
    return {"message": "Recipe saved successfully"}


@app.get("/api/sessions")
async def get_sessions():
    """Get all active sessions"""
    return {
        "sessions": [
            {
                "session_id": session_id,
                "recipe_name": session.recipe_name,
                "current_step": session.current_step,
                "completed": session.completed
            }
            for session_id, session in active_sessions.items()
        ]
    }


@app.get("/api/events")
async def events():
    """SSE endpoint for real-time events"""
    queue = asyncio.Queue()
    sse_connections.append(queue)
    
    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "message",
                        "data": data
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "ping",
                        "data": "keepalive"
                    }
        except Exception as e:
            print(f"SSE connection error: {e}")
        finally:
            if queue in sse_connections:
                sse_connections.remove(queue)
    
    return EventSourceResponse(event_generator())


# LiveKit agent integration
class MockJobContext:
    """Mock JobContext for testing without LiveKit"""
    def __init__(self):
        self.room = None
    
    async def connect(self, auto_subscribe=None):
        pass


@app.post("/api/agent/start")
async def start_agent():
    """Start the LiveKit agent"""
    try:
        # Create mock context for now
        ctx = MockJobContext()
        await entrypoint(ctx)
        return {"message": "Agent started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 