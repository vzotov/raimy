"""
MCP Server for Raimy Cooking Assistant
Exposes cooking tools via Model Context Protocol using FastMCP
"""
import os
from typing import List, Optional
import aiohttp
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Raimy Cooking Assistant")

# Cache for service token
_service_token_cache = None
_token_fetch_lock = None


async def get_service_token() -> Optional[str]:
    """Get JWT token for service authentication using API key"""
    global _service_token_cache, _token_fetch_lock
    import asyncio

    if _token_fetch_lock is None:
        _token_fetch_lock = asyncio.Lock()

    async with _token_fetch_lock:
        if _service_token_cache:
            return _service_token_cache

        for attempt in range(3):
            try:
                auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
                service_api_key = os.getenv("SERVICE_API_KEY")

                if not service_api_key:
                    print("⚠️  SERVICE_API_KEY not set - service authentication unavailable")
                    return None

                print(f"🔄 Attempting service authentication (attempt {attempt + 1}/3)")

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
                                print("✅ Service authentication successful")
                                return token
                        else:
                            error_text = await response.text()
                            print(f"❌ Service authentication failed: {response.status} - {error_text}")

                            if response.status in [401, 403]:
                                return None

            except Exception as e:
                print(f"❌ Error getting service token (attempt {attempt + 1}): {e}")

                if attempt < 2:
                    wait_time = (2 ** attempt)
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)

        print("❌ Failed to get service token after 3 attempts")
        return None


@mcp.tool()
async def set_ingredients(ingredients: List[dict]) -> dict:
    """
    Set the complete ingredients list for the current recipe.

    IMPORTANT WORKFLOW RULES:
    - Call this ONCE per session, immediately after send_recipe_name
    - Never call set_ingredients more than once - use update_ingredients for changes
    - Include the FULL ingredient list with all items needed for the recipe
    - Do NOT set highlighted or used flags initially (leave them out or false)

    REQUIRED FIELDS:
    Each ingredient must include:
    - name (str): Ingredient name (REQUIRED)
    - At least ONE of: amount (str) OR unit (str) (at least one is REQUIRED)

    OPTIONAL FIELDS:
    - highlighted (bool): Whether to highlight (default: false, don't set initially)
    - used (bool): Whether ingredient is used (default: false, don't set initially)

    Args:
        ingredients: List of ingredient dictionaries

    Returns:
        dict: Success status and message

    Valid Examples:
        set_ingredients([
            {"name": "eggs", "amount": "4"},
            {"name": "salt", "unit": "to taste"},
            {"name": "milk", "amount": "200", "unit": "ml"}
        ])
    """
    print(f"🔧 MCP TOOL: set_ingredients({len(ingredients)} items)")

    try:
        api_url = os.getenv("API_URL", "http://raimy-api:8000")

        # Filter out None values from each ingredient
        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes/ingredients",
                json={
                    "ingredients": ingredients_clean,
                    "action": "set"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ set_ingredients: {result.get('message')}")
                    return {
                        "success": True,
                        "message": result.get("message", f"Set {len(ingredients)} ingredients")
                    }
                else:
                    print(f"❌ set_ingredients failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "message": f"Failed: HTTP {response.status}"
                    }
    except Exception as e:
        print(f"❌ set_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def update_ingredients(ingredients: List[dict]) -> dict:
    """
    Update specific ingredients in the current recipe.

    Use this to highlight ingredients, mark them as used, or update quantities
    WITHOUT replacing the entire ingredient list.

    WORKFLOW RULES:
    - Use BEFORE a cooking step: Set highlighted=true for ingredients about to be used
    - Use AFTER a cooking step: Set highlighted=false and used=true for ingredients just used
    - Group all ingredient changes into a SINGLE update_ingredients call per step
    - Do NOT highlight all ingredients at once - only those needed for current step
    - NEVER narrate or mention highlighting to the user (it's UI-only)

    REQUIRED FIELDS:
    - name (str): Ingredient name (REQUIRED, used to match existing ingredient)

    OPTIONAL FIELDS:
    - amount (str): New quantity
    - unit (str): New unit
    - highlighted (bool): true to highlight, false to unhighlight
    - used (bool): true to mark as used

    Args:
        ingredients: List of ingredient dictionaries to update

    Returns:
        dict: Success status and message

    Example Workflow:
        # Before step: Highlight ingredients
        update_ingredients([{"name": "eggs", "highlighted": true}])

        # After step: Mark as used and unhighlight
        update_ingredients([
            {"name": "eggs", "highlighted": false, "used": true}
        ])
    """
    print(f"🔧 MCP TOOL: update_ingredients({len(ingredients)} items)")

    try:
        api_url = os.getenv("API_URL", "http://raimy-api:8000")

        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes/ingredients",
                json={
                    "ingredients": ingredients_clean,
                    "action": "update"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ update_ingredients: {result.get('message')}")
                    return {
                        "success": True,
                        "message": result.get("message", f"Updated {len(ingredients)} ingredients")
                    }
                else:
                    print(f"❌ update_ingredients failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "message": f"Failed: HTTP {response.status}"
                    }
    except Exception as e:
        print(f"❌ update_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def set_timer(duration: int, label: str) -> dict:
    """
    Set a cooking timer with a descriptive label.

    WORKFLOW RULES:
    - ONLY use for PASSIVE, time-dependent cooking actions (boiling, baking, simmering, frying, resting, chilling)
    - NEVER use for active tasks controlled by the user (mixing, whisking, stirring, chopping, peeling, seasoning)
    - DO NOT estimate how long user tasks take - let them work at their own pace
    - ALWAYS narrate when setting a timer (e.g., "Set a 5-minute timer to simmer the sauce")
    - While timer runs, you can guide user on safe parallel prep tasks

    Args:
        duration: Timer duration in seconds (REQUIRED)
        label: Descriptive label using infinitive form, e.g., "to flip", "to simmer" (REQUIRED)

    Returns:
        dict: Success status and message

    Examples:
        ✅ CORRECT: set_timer(duration=300, label="to simmer sauce")
        ✅ CORRECT: set_timer(duration=600, label="to boil pasta")
        ❌ WRONG: set_timer(duration=90, label="to beat eggs")  # Active task!
    """
    print(f"🔧 MCP TOOL: set_timer({duration}s, '{label}')")

    try:
        api_url = os.getenv("API_URL", "http://raimy-api:8000")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/timers/set",
                json={"duration": duration, "label": label}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ set_timer: {result.get('message')}")
                    return {
                        "success": True,
                        "message": result.get("message", f"Timer set: {duration}s - {label}")
                    }
                else:
                    print(f"❌ set_timer failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "message": f"Failed: HTTP {response.status}"
                    }
    except Exception as e:
        print(f"❌ set_timer error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def send_recipe_name(recipe_name: str) -> dict:
    """
    Display the recipe name to the user.

    Call this at the beginning of cooking to show what recipe is being prepared.

    Args:
        recipe_name: Name of the recipe being prepared

    Returns:
        dict: Success status and message

    Example:
        send_recipe_name("Spaghetti Carbonara")
    """
    print(f"🔧 MCP TOOL: send_recipe_name('{recipe_name}')")

    try:
        api_url = os.getenv("API_URL", "http://raimy-api:8000")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes/name",
                json={"recipe_name": recipe_name}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ send_recipe_name: {result.get('message')}")
                    return {
                        "success": True,
                        "message": result.get("message", f"Recipe name sent: {recipe_name}")
                    }
                else:
                    print(f"❌ send_recipe_name failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "message": f"Failed: HTTP {response.status}"
                    }
    except Exception as e:
        print(f"❌ send_recipe_name error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def save_recipe(recipe_data: str) -> dict:
    """
    Save a complete recipe to the database for future reference.

    Use this when the user has finished cooking and wants to save the recipe.

    Args:
        recipe_data: Complete recipe information including ingredients and steps

    Returns:
        dict: Success status, recipe ID, and message

    Example:
        save_recipe("Spaghetti Carbonara: Boil pasta for 10 minutes...")
    """
    print(f"🔧 MCP TOOL: save_recipe('{recipe_data[:50]}...')")

    try:
        api_url = os.getenv("API_URL", "http://raimy-api:8000")
        user_id = "service@raimy.internal"

        recipe_data_obj = {
            "name": "Raimy Generated Recipe",
            "description": recipe_data,
            "ingredients": ["See recipe description"],
            "steps": [{"instruction": recipe_data, "duration_minutes": 5}],
            "total_time_minutes": 30,
            "difficulty": "medium",
            "servings": 4,
            "tags": ["raimy-generated"],
            "user_id": user_id
        }

        # Get service authentication
        auth_token = await get_service_token()
        headers = {}

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            print("⚠️  WARNING: No service token - recipe save may fail")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/recipes",
                json=recipe_data_obj,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    recipe_id = result.get("recipe_id")
                    print(f"✅ save_recipe: Recipe saved with ID {recipe_id}")
                    return {
                        "success": True,
                        "recipe_id": recipe_id,
                        "message": result.get("message", "Recipe saved successfully")
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', 'Unknown error')
                    print(f"❌ save_recipe failed: {error_msg}")
                    return {
                        "success": False,
                        "message": f"Failed: {error_msg}"
                    }
    except Exception as e:
        print(f"❌ save_recipe error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def generate_session_name(conversation_summary: str, session_id: str) -> dict:
    """
    Generate a concise 3-5 word name for a meal planning session.

    WHEN TO USE:
    - Call automatically after first 2-3 message exchanges in a meal planner session
    - Only call ONCE per session when it still has default name "Untitled Session"
    - Do NOT mention this to the user - it happens silently

    NAMING GUIDELINES:
    - Keep it 3-5 words maximum
    - Make it descriptive of the meal/recipe being planned
    - Use title case (e.g., "Thai Curry Recipe", "Weekly Meal Prep")
    - Avoid generic names like "Meal Plan" or "Recipe Ideas"

    Args:
        conversation_summary: Brief summary of what user wants to plan (2-3 sentences)
        session_id: The session ID to update

    Returns:
        dict with success status and generated session_name

    Examples:
        "Thai Curry Recipe"
        "Weekly Meal Prep"
        "Dinner Party Planning"
        "Healthy Lunch Ideas"
    """
    print(f"🔧 MCP TOOL: generate_session_name(session_id={session_id})")

    try:
        # Use a simple LLM call to generate name
        from livekit.plugins import openai as openai_plugin

        llm = openai_plugin.LLM(model="gpt-4o-mini")

        prompt = f"""Generate a concise 3-5 word name for this meal planning session.

Conversation Summary:
{conversation_summary}

Requirements:
- Maximum 5 words
- Title case
- Descriptive and specific
- No generic terms

Respond with ONLY the session name, nothing else."""

        # Generate name using LLM
        response = await llm.chat(prompt)
        session_name = response.content.strip().strip('"').strip("'")

        # Validate length
        word_count = len(session_name.split())
        if word_count > 6:
            # Truncate to first 5 words
            session_name = " ".join(session_name.split()[:5])

        print(f"✅ Generated session name: '{session_name}'")

        # Update session name via API
        api_url = os.getenv("API_URL", "http://raimy-api:8000")
        auth_token = await get_service_token()
        headers = {}

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            print("⚠️  WARNING: No service token - session name update may fail")

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{api_url}/api/meal-planner-sessions/{session_id}/name",
                json={"session_name": session_name},
                headers=headers
            ) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "session_name": session_name,
                        "message": f"Session renamed to: {session_name}"
                    }
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to update session name: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "session_name": session_name,
                        "message": f"Generated name but failed to save: {error_text}"
                    }

    except Exception as e:
        print(f"❌ generate_session_name error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    # Run the MCP server with Streamable HTTP transport
    # This makes it accessible over HTTP for both LiveKit and OpenAI Agent Builder
    print("🚀 Starting Raimy MCP Server on HTTP (Streamable HTTP transport)...")

    # FastMCP 2.0 uses http_app() to create an ASGI application
    mcp_app = mcp.http_app()

    # Wrap with FastAPI to add health endpoint
    app = FastAPI()

    @app.get("/health")
    async def health_check():
        return JSONResponse({"status": "healthy", "service": "mcp"})

    # Mount MCP app at /mcp
    app.mount("/mcp", mcp_app)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
