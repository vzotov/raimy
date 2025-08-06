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
    print(f"🔧 TOOL CALL: set_timer(duration={duration}, label='{label}')", flush=True)
    
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
                    print(f"✅ TOOL RESULT: set_timer - Success: {result.get('message', f'Timer set for {duration} seconds: {label}')}", flush=True)
                    return None
                else:
                    print(f"❌ TOOL RESULT: set_timer - Failed: HTTP {response.status}", flush=True)
                    return None
    except Exception as e:
        print(f"❌ TOOL RESULT: set_timer - Error: {str(e)}", flush=True)
        return None


@function_tool
async def send_recipe_name(
    context: RunContext,
    recipe_name: str,
):
    """Send the recipe name to the client via SSE broadcast."""
    print(f"🔧 TOOL CALL: send_recipe_name(recipe_name='{recipe_name}')", flush=True)
    
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
                    print(f"✅ TOOL RESULT: send_recipe_name - Success: {result.get('message', f'Recipe name sent: {recipe_name}')}", flush=True)
                    return {
                        "success": True,
                        "message": result.get("message", f"Recipe name sent: {recipe_name}")
                    }
                else:
                    print(f"❌ TOOL RESULT: send_recipe_name - Failed: HTTP {response.status}", flush=True)
                    return {
                        "success": False,
                        "message": f"Failed to send recipe name: HTTP {response.status}"
                    }
    except Exception as e:
        print(f"❌ TOOL RESULT: send_recipe_name - Error: {str(e)}", flush=True)
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
    print(f"🔧 TOOL CALL: save_recipe(recipe_data='{recipe_data[:100]}{'...' if len(recipe_data) > 100 else ''}')", flush=True)
    
    try:
        # Get API URL from environment variable
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # For now, use anonymous user ID
        user_id = "anonymous"
        
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
                    print(f"✅ TOOL RESULT: save_recipe - Success: Recipe ID {result.get('recipe_id')}", flush=True)
                    return None
                else:
                    error_data = await response.json()
                    print(f"❌ TOOL RESULT: save_recipe - Failed: {error_data.get('detail', 'Unknown error')}", flush=True)
                    return None
    except Exception as e:
        print(f"❌ TOOL RESULT: save_recipe - Error: {str(e)}", flush=True)
        return None 