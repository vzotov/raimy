from fastapi import APIRouter
from typing import List
import asyncio

from .models import TimerRequest

# Import broadcast_event from main API
broadcast_event = None

router = APIRouter(prefix="/api/timers", tags=["timers"])


@router.post("/set")
async def set_timer(timer_request: dict):
    """Set a timer for the current cooking step"""
    duration = timer_request.get("duration")
    label = timer_request.get("label")
    session_id = timer_request.get("session_id")

    # Send via WebSocket to specific session
    if session_id:
        from app.main import connection_manager
        timer_data = {
            "duration": duration,
            "label": label,
            "started_at": asyncio.get_event_loop().time()
        }

        await connection_manager.send_message(session_id, {
            "type": "agent_message",
            "content": {
                "type": "timer",
                "duration": duration,
                "label": label,
                "started_at": timer_data["started_at"]
            }
        })

    return {"message": f"Timer set for {duration} seconds: {label}"}


def create_timers_router(broadcast_func):
    """Create timers router with injected broadcast function"""
    global broadcast_event
    broadcast_event = broadcast_func
    return router 