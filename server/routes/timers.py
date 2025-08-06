from fastapi import APIRouter
from typing import List
import asyncio

from .models import TimerRequest

# Import broadcast_event from main API
broadcast_event = None

router = APIRouter(prefix="/api/timers", tags=["timers"])


@router.post("/set")
async def set_timer(timer: TimerRequest):
    """Set a timer for the current cooking step"""
    timer_data = {
        "duration": timer.duration,
        "label": timer.label,
        "started_at": asyncio.get_event_loop().time()
    }
    
    # Broadcast timer set event
    if broadcast_event:
        await broadcast_event("timer_set", timer_data)
    
    return {"message": f"Timer set for {timer.duration} seconds: {timer.label}"}


def create_timers_router(broadcast_func):
    """Create timers router with injected broadcast function"""
    global broadcast_event
    broadcast_event = broadcast_func
    return router 