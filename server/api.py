import asyncio
import json
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import uvicorn


# Data models
class TimerRequest(BaseModel):
    duration: int
    label: str


# Global state for SSE connections
sse_connections: List[asyncio.Queue] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FastAPI server...")
    yield
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
    allow_origins=["*"],
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


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 