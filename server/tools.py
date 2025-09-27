import aiohttp
import os
from livekit.agents import function_tool, RunContext
from typing import List, Optional
from dataclasses import dataclass, asdict

# Cache for service token to avoid repeated requests
_service_token_cache = None
_token_fetch_lock = None

async def get_service_token() -> Optional[str]:
    """Get JWT token for service authentication using API key"""
    global _service_token_cache, _token_fetch_lock

    # Import asyncio inside function to avoid circular imports
    import asyncio

    # Initialize lock if not exists
    if _token_fetch_lock is None:
        _token_fetch_lock = asyncio.Lock()

    # Use lock to prevent multiple simultaneous token requests
    async with _token_fetch_lock:
        # Check cache again inside lock (another request might have fetched it)
        if _service_token_cache:
            return _service_token_cache

        # Try multiple times with exponential backoff
        for attempt in range(3):
            try:
                # Use auth service directly for service authentication
                auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
                service_api_key = os.getenv("SERVICE_API_KEY")

                if not service_api_key:
                    print("⚠️  SERVICE_API_KEY not set - service authentication unavailable", flush=True)
                    return None

                print(f"🔄 Attempting service authentication (attempt {attempt + 1}/3) to {auth_service_url}", flush=True)

                # Add timeout and retry logic
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{auth_service_url}/auth/service-auth",
                        headers={"x-api-key": service_api_key}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            token = result.get("token")
                            if token:
                                _service_token_cache = token
                                print("✅ Service authentication successful", flush=True)
                                return token
                        else:
                            error_text = await response.text()
                            print(f"❌ Service authentication failed: {response.status} - {error_text}", flush=True)

                            # Don't retry on 401/403 - these are auth failures
                            if response.status in [401, 403]:
                                return None

            except Exception as e:
                print(f"❌ Error getting service token (attempt {attempt + 1}): {e}", flush=True)

                # Wait before retrying (exponential backoff)
                if attempt < 2:
                    wait_time = (2 ** attempt)
                    print(f"⏳ Waiting {wait_time}s before retry...", flush=True)
                    await asyncio.sleep(wait_time)

        print("❌ Failed to get service token after 3 attempts", flush=True)
        return None

@dataclass
class Ingredient:
    name: str
    amount: Optional[str] = None
    unit: Optional[str] = None
    highlighted: Optional[bool] = None
    used: Optional[bool] = None

@function_tool
async def set_ingredients(
    context: RunContext,
    ingredients: List[Ingredient],
):
    """Set the complete ingredients list for the current recipe. Use this for the initial list of all ingredients."""
    print(f"🔧 TOOL CALL: set_ingredients(ingredients={len(ingredients)} items)", flush=True)

    try:
        # Get API URL from environment variable
        api_url = os.getenv("API_URL", "http://localhost:8000")

        # Convert dataclass objects to dictionaries, filtering out None values
        ingredients_dict = []
        for ingredient in ingredients:
            # Use dataclasses.asdict() and filter out None values
            ingredient_dict = {k: v for k, v in asdict(ingredient).items() if v is not None}
            ingredients_dict.append(ingredient_dict)

        # Call our API to broadcast the ingredients event
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes/ingredients",
                json={
                    "ingredients": ingredients_dict,
                    "action": "set"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ TOOL RESULT: set_ingredients - Success: {result.get('message', f'Ingredients set: {len(ingredients)} items')}", flush=True)
                    return {
                        "success": True,
                        "message": result.get("message", f"Ingredients set: {len(ingredients)} items")
                    }
                else:
                    print(f"❌ TOOL RESULT: set_ingredients - Failed: HTTP {response.status}", flush=True)
                    return None
    except Exception as e:
        print(f"❌ TOOL RESULT: set_ingredients - Error: {str(e)}", flush=True)
        return None


@function_tool
async def update_ingredients(
    context: RunContext,
    ingredients: List[Ingredient],
):
    """Update specific ingredients in the current recipe. Use this for highlighting, marking as used, or updating specific ingredients."""
    print(f"🔧 TOOL CALL: update_ingredients(ingredients={len(ingredients)} items)", flush=True)

    try:
        # Get API URL from environment variable
        api_url = os.getenv("API_URL", "http://localhost:8000")

        # Convert dataclass objects to dictionaries, filtering out None values
        ingredients_dict = []
        for ingredient in ingredients:
            # Use dataclasses.asdict() and filter out None values
            ingredient_dict = {k: v for k, v in asdict(ingredient).items() if v is not None}
            ingredients_dict.append(ingredient_dict)

        # Call our API to broadcast the ingredients update event
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes/ingredients",
                json={
                    "ingredients": ingredients_dict,
                    "action": "update"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ TOOL RESULT: update_ingredients - Success: {result.get('message', f'Ingredients updated: {len(ingredients)} items')}", flush=True)
                    return {
                        "success": True,
                        "message": result.get("message", f"Ingredients updated: {len(ingredients)} items")
                    }
                else:
                    print(f"❌ TOOL RESULT: update_ingredients - Failed: HTTP {response.status}", flush=True)
                    return None
    except Exception as e:
        print(f"❌ TOOL RESULT: update_ingredients - Error: {str(e)}", flush=True)
        return None


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

        # Use service account identifier - will be refactored with PostgreSQL
        user_id = "service@raimy.internal"

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

        # Get service authentication
        auth_token = await get_service_token()
        headers = {}

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            print("⚠️  WARNING: Could not get service token - recipe save may fail", flush=True)

        # Call our API to save the recipe
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes",
                json=recipe_data_obj,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ TOOL RESULT: save_recipe - Success: Recipe ID {result.get('recipe_id')}", flush=True)
                    return {
                        "success": True,
                        "recipe_id": result.get("recipe_id"),
                        "message": result.get("message", "Recipe saved successfully")
                    }
                else:
                    error_data = await response.json()
                    print(f"❌ TOOL RESULT: save_recipe - Failed: {error_data.get('detail', 'Unknown error')}", flush=True)
                    return None
    except Exception as e:
        print(f"❌ TOOL RESULT: save_recipe - Error: {str(e)}", flush=True)
        return None