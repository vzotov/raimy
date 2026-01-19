"""
MCP Server for Raimy Cooking Assistant
Exposes cooking tools via Model Context Protocol using FastMCP
"""
import os
import sys
from typing import List, Optional
import aiohttp
from fastmcp import FastMCP
import logging

# Add server directory to path to import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.redis_client import get_redis_client

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Raimy Cooking Assistant")

# Initialize Redis client
redis_client = get_redis_client()

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


@mcp.tool(tags={"kitchen"})
async def set_ingredients(ingredients: List[dict], session_id: str) -> dict:
    """
    Set the complete ingredients list for the current recipe.

    ⚠️ CALL EXACTLY ONCE per cooking session, immediately after set_session_name.
    DO NOT call again if you've already set ingredients in this conversation.
    Use update_ingredients() for any changes after initial setup.

    IMPORTANT WORKFLOW RULES:
    - Include the FULL ingredient list with all items needed for the recipe
    - Do NOT set highlighted or used flags initially (leave them out or false)

    REQUIRED FIELDS:
    Each ingredient must include:
    - name (str): Ingredient name (REQUIRED)
    - At least ONE of: amount (str) OR unit (str) (at least one is REQUIRED)
    - unit MUST ALWAYS be in English (g, ml, tbsp, cup, etc.) regardless of recipe language
    - Do NOT use "pcs", "шт." or similar - for countable items, just use amount without unit

    OPTIONAL FIELDS:
    - eng_name (str): English name for Instacart (only if name is NOT in English)
    - highlighted (bool): Whether to highlight (default: false, don't set initially)
    - used (bool): Whether ingredient is used (default: false, don't set initially)

    Args:
        ingredients: List of ingredient dictionaries
        session_id: Session ID for WebSocket routing (injected automatically by agent)

    Returns:
        dict: Success status and message

    Valid Examples:
        set_ingredients([
            {"name": "eggs", "amount": "4"},
            {"name": "salt", "unit": "to taste"},
            {"name": "milk", "amount": "200", "unit": "ml"},
            {"name": "яйца", "eng_name": "eggs", "amount": "4"}
        ])
    """
    print(f"🔧 MCP TOOL: set_ingredients({len(ingredients)} items, session={session_id})")

    try:
        # Filter out None values from each ingredient
        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        # Publish to Redis using helper method
        await redis_client.send_ingredients_message(
            session_id,
            ingredients_clean,
            action="set"
        )

        print(f"✅ set_ingredients: Set {len(ingredients)} ingredients")
        return {
            "success": True,
            "message": f"Set {len(ingredients)} ingredients"
        }
    except Exception as e:
        print(f"❌ set_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"kitchen"})
async def update_ingredients(ingredients: List[dict], session_id: str) -> dict:
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
        session_id: Session ID for WebSocket routing (injected automatically by agent)

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
    print(f"🔧 MCP TOOL: update_ingredients({len(ingredients)} items, session={session_id})")

    try:
        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        # Publish to Redis using helper method
        await redis_client.send_ingredients_message(
            session_id,
            ingredients_clean,
            action="update"
        )

        print(f"✅ update_ingredients: Updated {len(ingredients)} ingredients")
        return {
            "success": True,
            "message": f"Updated {len(ingredients)} ingredients"
        }
    except Exception as e:
        print(f"❌ update_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"kitchen"})
async def set_timer(duration: int, label: str, session_id: str) -> dict:
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
        session_id: Session ID for WebSocket routing (injected automatically by agent)

    Returns:
        dict: Success status and message

    Examples:
        ✅ CORRECT: set_timer(duration=300, label="to simmer sauce")
        ✅ CORRECT: set_timer(duration=600, label="to boil pasta")
        ❌ WRONG: set_timer(duration=90, label="to beat eggs")  # Active task!
    """
    print(f"🔧 MCP TOOL: set_timer({duration}s, '{label}', session={session_id})")

    try:
        # Publish to Redis using helper method
        await redis_client.send_timer_message(session_id, duration, label)

        print(f"✅ set_timer: Timer set: {duration}s - {label}")
        return {
            "success": True,
            "message": f"Timer set: {duration}s - {label}"
        }
    except Exception as e:
        print(f"❌ set_timer error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"kitchen", "recipe-creator"})
async def set_session_name(session_name: str, session_id: str) -> dict:
    """
    Set/display the session name for kitchen or meal planner sessions.

    Use this to show the user what they're working on - a recipe name in kitchen mode,
    or a meal plan name in meal planner mode.

    ⚠️ CALL EXACTLY ONCE per session when the topic/recipe is first established.
    DO NOT call again if you've already set the session name in this conversation.

    Args:
        session_name: Name of the session (recipe name or meal plan name)
        session_id: Session ID for WebSocket routing (injected automatically by agent)

    Returns:
        dict: Success status and message

    Example:
        set_session_name("Spaghetti Carbonara")
        set_session_name("Weekly Meal Plan")
    """
    print(f"🔧 MCP TOOL: set_session_name('{session_name}', session={session_id})")

    try:
        # Publish to Redis using helper method
        await redis_client.send_session_name_message(session_id, session_name)

        print(f"✅ set_session_name: Session name set: {session_name}")
        return {
            "success": True,
            "message": f"Session name set: {session_name}"
        }
    except Exception as e:
        print(f"❌ set_session_name error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"recipe-creator"})
async def set_recipe_metadata(
    session_id: str,
    name: str,
    description: Optional[str] = None,
    difficulty: Optional[str] = None,
    total_time_minutes: Optional[int] = None,
    servings: Optional[int] = None,
    tags: Optional[str] = None,
) -> dict:
    """
    Set or update recipe metadata in the meal planner sidebar.

    Use this to initialize a recipe or update its properties. This replaces
    ALL metadata fields, so include all values you want to keep.

    Args:
        name: Recipe name (REQUIRED)
        description: Recipe description
        difficulty: Difficulty level (string: 'easy', 'medium', or 'hard')
        total_time_minutes: Total cooking time in minutes (integer: 30, 60, 90, etc.)
        servings: Number of servings (integer: 4, 6, 8, etc.)
        tags: Comma-separated tags (e.g., 'italian, pasta, quick')
        session_id: Session ID (auto-injected)

    Example:
        set_recipe_metadata(
            name='Pasta Carbonara',
            description='Classic Italian pasta dish',
            difficulty='medium',
            total_time_minutes=30,
            servings=4,
            tags='italian, pasta'
        )
    """
    print(f"🔧 MCP TOOL: set_recipe_metadata(name='{name}', session={session_id})")

    try:
        # Parse comma-separated tags into array
        tags_array = [tag.strip() for tag in tags.split(',')] if tags else []

        await redis_client.send_recipe_metadata_message(
            session_id,
            name=name,
            description=description,
            difficulty=difficulty,
            total_time_minutes=total_time_minutes,
            servings=servings,
            tags=tags_array
        )

        print(f"✅ set_recipe_metadata: Updated metadata for '{name}'")
        return {"success": True, "message": f"Recipe metadata updated: {name}"}
    except Exception as e:
        print(f"❌ set_recipe_metadata error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"recipe-creator"})
async def set_recipe_ingredients(
    session_id: str,
    ingredients: List[dict],
) -> dict:
    """
    Set the complete ingredients list for the meal planner recipe.

    This REPLACES the entire ingredients list. To add or modify ingredients,
    send the full updated list including existing items.

    Args:
        ingredients: Complete list of ingredients (use same structure as set_ingredients tool)
                    Each ingredient MUST have:
                      - name (str, REQUIRED)
                      - At least ONE of: amount (str) OR unit (str)
                      - unit MUST ALWAYS be in English (g, ml, tbsp, cup, etc.)
                      - Do NOT use "pcs", "шт." - for countable items, just use amount
                    Optional fields:
                      - eng_name (str): English name for Instacart (only if name is NOT in English)
                      - notes (str)
        session_id: Session ID (auto-injected)

    Example:
        set_recipe_ingredients([
            {"name": "spaghetti", "amount": "400", "unit": "g"},
            {"name": "eggs", "amount": "4"},
            {"name": "salt", "unit": "to taste"},
            {"name": "яйца", "eng_name": "eggs", "amount": "4"}
        ])
    """
    print(f"🔧 MCP TOOL: set_recipe_ingredients({len(ingredients)} items, session={session_id})")

    try:
        # Clean ingredients - remove None values
        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        await redis_client.send_recipe_ingredients_message(session_id, ingredients_clean)

        print(f"✅ set_recipe_ingredients: Set {len(ingredients)} ingredients")
        return {"success": True, "message": f"Set {len(ingredients)} ingredients"}
    except Exception as e:
        print(f"❌ set_recipe_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"recipe-creator"})
async def set_recipe_steps(
    session_id: str,
    steps: List[dict],
) -> dict:
    """
    Set the complete cooking steps for the meal planner recipe.

    This REPLACES the entire steps list. To add or modify steps,
    send the full updated list including existing items.

    Args:
        steps: Complete list of cooking steps. Each step must have:
               - instruction (str, REQUIRED): The step instruction
               - duration (int, OPTIONAL): Duration in minutes for this step
        session_id: Session ID (auto-injected)

    Example:
        set_recipe_steps([
            {"instruction": "Boil pasta in salted water", "duration": 10},
            {"instruction": "Mix eggs with grated parmesan cheese", "duration": 2},
            {"instruction": "Drain pasta and combine with egg mixture", "duration": 1},
            {"instruction": "Serve hot with black pepper"}
        ])
    """
    logger.info(f"🔧 MCP TOOL: set_recipe_steps({len(steps)} steps, session={session_id})")

    try:
        # Validate step format
        normalized_steps = []
        for i, step in enumerate(steps):
            if isinstance(step, str):
                # Legacy format: convert string to dict
                normalized_steps.append({"instruction": step})
                logger.warning(f"Step {i+1}: Converted legacy string format to dict")
            elif isinstance(step, dict):
                if "instruction" not in step:
                    raise ValueError(f"Step {i+1} missing required 'instruction' field")
                # Normalize to only include instruction and duration
                normalized_step = {"instruction": step["instruction"]}
                if "duration" in step and step["duration"] is not None:
                    normalized_step["duration"] = step["duration"]
                normalized_steps.append(normalized_step)
            else:
                raise ValueError(f"Step {i+1} has invalid format: {type(step)}")

        await redis_client.send_recipe_steps_message(session_id, normalized_steps)

        logger.info(f"✅ set_recipe_steps: Set {len(normalized_steps)} steps")
        return {"success": True, "message": f"Set {len(normalized_steps)} steps"}
    except Exception as e:
        logger.error(f"❌ set_recipe_steps error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool(tags={"recipe-creator"})
async def save_recipe(session_id: str) -> dict:
    """
    Save the current recipe to the user's recipe collection.

    The recipe data is read from the session (which you've been building using
    set_recipe_metadata, set_recipe_ingredients, and set_recipe_steps).

    CRITICAL RULES:
    - NEVER call set_recipe_metadata, set_recipe_ingredients, or set_recipe_steps in the same turn as save_recipe
    - ONLY call save_recipe by itself - do not combine with other recipe tools
    - If you need to update the recipe, do it in a separate turn BEFORE asking to save

    WORKFLOW:
    1. Build recipe using the 3 recipe tools (metadata, ingredients, steps) - separate turn
    2. ASK user: "Would you like me to save this recipe to your collection?"
    3. If yes, call ONLY save_recipe (no other tools in this turn)

    IMPORTANT: Can be called multiple times to update a saved recipe after edits.

    Args:
        session_id: Session ID (injected automatically by agent)

    Returns:
        dict: Success status and message

    Example - CORRECT:
        Turn 1: set_recipe_metadata(...), set_recipe_ingredients(...), set_recipe_steps(...)
        Turn 2: save_recipe(session_id="abc-123")  # ONLY this tool, nothing else

    Example - WRONG:
        set_recipe_metadata(...) + save_recipe(...)  # ❌ DON'T DO THIS
    """
    logger.info(f"🔧 MCP TOOL: save_recipe called with session_id='{session_id}'")

    try:
        await redis_client.send_recipe_save_request(session_id)
        logger.info(f"✅ Recipe save request published to Redis")

        return {
            "success": True,
            "message": "Recipe save initiated. You'll receive confirmation shortly."
        }
    except Exception as e:
        logger.error(f"❌ MCP: save_recipe exception: {str(e)}", exc_info=True)
        return {"success": False, "message": f"Error: {str(e)}"}


# NOTE: generate_session_name tool removed - was using deprecated LiveKit plugin
# Session names can be updated manually by the user via the UI


if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse

    # Run the MCP server with stateless HTTP transport
    print("🚀 Starting Raimy MCP Server on HTTP (stateless HTTP transport)...")

    # FastMCP 2.0 uses http_app() to create an ASGI application
    # Use stateless_http=True to avoid session management complexity
    mcp_app = mcp.http_app(stateless_http=True)

    # Add health check route
    async def health_check(request):
        return JSONResponse({"status": "healthy", "service": "mcp"})

    # Create app with both MCP and health endpoints
    # IMPORTANT: Must pass lifespan from mcp_app to parent Starlette app
    app = Starlette(
        routes=[
            Route("/health", health_check),
            Mount("/", app=mcp_app),
        ],
        lifespan=mcp_app.lifespan
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
