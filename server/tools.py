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


@function_tool
async def send_recipe_name(
    context: RunContext,
    recipe_name: str,
):
    """Send the recipe name to the client via SSE broadcast."""
    try:
        # Get API URL from environment variable
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Call our API to broadcast the recipe name event
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes/name",
                json={
                    "recipe_name": recipe_name
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": result.get("message", f"Recipe name sent: {recipe_name}")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send recipe name: HTTP {response.status}"
                    }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending recipe name: {str(e)}"
        } 