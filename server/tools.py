import aiohttp
import os
from typing import List, Dict, Any
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


@function_tool
async def save_recipe(
    context: RunContext,
    recipe_data: str,
):
    """Save a complete recipe to the database. Use this when the recipe is fully explained and ready to be saved."""
    try:
        # Get API URL from environment variable
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Get user ID from LiveKit context
        user_id = "anonymous"
        if context.room and context.room.participants:
            # Get the first non-agent participant (the user)
            for participant in context.room.participants.values():
                if not participant.identity.startswith(('agent', 'assistant', 'raimy')):
                    user_id = participant.identity
                    break
        
        # Prepare simple recipe data for testing
        recipe_data_obj = {
            "name": "Test Recipe",
            "description": recipe_data,
            "ingredients": ["test ingredient"],
            "steps": [{"instruction": "test step", "duration_minutes": 5}],
            "total_time_minutes": 10,
            "difficulty": "easy",
            "servings": 2,
            "tags": ["raimy-generated"],
            "user_id": user_id
        }
        
        # Call our API to save the recipe
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes",
                json=recipe_data_obj
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": f"Recipe saved successfully! Recipe ID: {result.get('recipe_id')}",
                        "recipe_id": result.get("recipe_id")
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to save recipe: {error_data.get('detail', 'Unknown error')}"
                    }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error saving recipe: {str(e)}"
        } 