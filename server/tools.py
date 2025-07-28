import aiohttp
import os
from livekit.agents import function_tool, RunContext


@function_tool
async def set_timer(
    context: RunContext,
    duration: int,
    label: str,
):
    """Set a timer for the specified duration (in seconds) and provide a descriptive label."""
    try:
        # Get API URL from environment variable
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Call our API to broadcast the timer event
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/timers/set",
                json={
                    "duration": duration,
                    "label": label
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": result.get("message", f"Timer set for {duration} seconds: {label}")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to set timer: HTTP {response.status}"
                    }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error setting timer: {str(e)}"
        } 