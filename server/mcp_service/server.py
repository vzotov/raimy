"""
MCP Server for Raimy Cooking Assistant
Exposes cooking tools via Model Context Protocol using FastMCP
"""
import os
import sys
from typing import List, Optional
import aiohttp
from fastmcp import FastMCP

# Add server directory to path to import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.redis_client import get_redis_client

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


@mcp.tool()
async def set_ingredients(ingredients: List[dict], session_id: str) -> dict:
    """
    Set the complete ingredients list for the current recipe.

    ⚠️ CALL EXACTLY ONCE per cooking session, immediately after send_recipe_name.
    DO NOT call again if you've already set ingredients in this conversation.
    Use update_ingredients() for any changes after initial setup.

    IMPORTANT WORKFLOW RULES:
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
        session_id: Session ID for WebSocket routing (injected automatically by agent)

    Returns:
        dict: Success status and message

    Valid Examples:
        set_ingredients([
            {"name": "eggs", "amount": "4"},
            {"name": "salt", "unit": "to taste"},
            {"name": "milk", "amount": "200", "unit": "ml"}
        ])
    """
    print(f"🔧 MCP TOOL: set_ingredients({len(ingredients)} items, session={session_id})")

    try:
        # Filter out None values from each ingredient
        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        # Publish to Redis instead of HTTP call
        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "ingredients",
                    "items": ingredients_clean,
                    "action": "set"
                }
            }
        )

        print(f"✅ set_ingredients: Set {len(ingredients)} ingredients")
        return {
            "success": True,
            "message": f"Set {len(ingredients)} ingredients"
        }
    except Exception as e:
        print(f"❌ set_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
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

        # Publish to Redis
        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "ingredients",
                    "items": ingredients_clean,
                    "action": "update"
                }
            }
        )

        print(f"✅ update_ingredients: Updated {len(ingredients)} ingredients")
        return {
            "success": True,
            "message": f"Updated {len(ingredients)} ingredients"
        }
    except Exception as e:
        print(f"❌ update_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
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
        # Publish to Redis
        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "timer",
                    "duration": duration,
                    "label": label
                }
            }
        )

        print(f"✅ set_timer: Timer set: {duration}s - {label}")
        return {
            "success": True,
            "message": f"Timer set: {duration}s - {label}"
        }
    except Exception as e:
        print(f"❌ set_timer error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def send_recipe_name(recipe_name: str, session_id: str) -> dict:
    """
    Display the recipe name to the user.

    ⚠️ CALL EXACTLY ONCE per cooking session when recipe is first selected.
    DO NOT call again if you've already sent the recipe name in this conversation.

    Args:
        recipe_name: Name of the recipe being prepared
        session_id: Session ID for WebSocket routing (injected automatically by agent)

    Returns:
        dict: Success status and message

    Example:
        send_recipe_name("Spaghetti Carbonara")
    """
    print(f"🔧 MCP TOOL: send_recipe_name('{recipe_name}', session={session_id})")

    try:
        # Publish to Redis
        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_name",
                    "name": recipe_name
                }
            }
        )

        print(f"✅ send_recipe_name: Recipe name sent: {recipe_name}")
        return {
            "success": True,
            "message": f"Recipe name sent: {recipe_name}"
        }
    except Exception as e:
        print(f"❌ send_recipe_name error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def set_recipe_metadata(
    session_id: str,
    name: str,
    description: Optional[str] = None,
    difficulty: Optional[str] = None,
    total_time: Optional[str] = None,
    servings: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    """
    Set or update recipe metadata in the meal planner sidebar.

    Use this to initialize a recipe or update its properties. This replaces
    ALL metadata fields, so include all values you want to keep.

    Args:
        name: Recipe name (REQUIRED)
        description: Recipe description
        difficulty: Difficulty level (string: 'easy', 'medium', or 'hard')
        total_time: Total cooking time (string: '30 minutes', '1 hour', etc.)
        servings: Number of servings (string: '4', '4-6 people', etc.)
        tags: List of tags (e.g., ['italian', 'pasta', 'quick'])
        session_id: Session ID (auto-injected)

    Example:
        set_recipe_metadata(
            name='Pasta Carbonara',
            description='Classic Italian pasta dish',
            difficulty='medium',
            total_time='30 minutes',
            servings='4',
            tags=['italian', 'pasta']
        )
    """
    print(f"🔧 MCP TOOL: set_recipe_metadata(name='{name}', session={session_id})")

    try:
        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_metadata",
                    "name": name,
                    "description": description,
                    "difficulty": difficulty,
                    "total_time": total_time,
                    "servings": servings,
                    "tags": tags or [],
                }
            }
        )

        print(f"✅ set_recipe_metadata: Updated metadata for '{name}'")
        return {"success": True, "message": f"Recipe metadata updated: {name}"}
    except Exception as e:
        print(f"❌ set_recipe_metadata error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
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
                    Optional fields:
                      - notes (str)
        session_id: Session ID (auto-injected)

    Example:
        set_recipe_ingredients([
            {"name": "spaghetti", "amount": "400", "unit": "g"},
            {"name": "eggs", "amount": "4"},
            {"name": "salt", "unit": "to taste"},
            {"name": "parmesan", "amount": "100", "unit": "g"}
        ])
    """
    print(f"🔧 MCP TOOL: set_recipe_ingredients({len(ingredients)} items, session={session_id})")

    try:
        # Clean ingredients - remove None values
        ingredients_clean = [
            {k: v for k, v in ing.items() if v is not None}
            for ing in ingredients
        ]

        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_ingredients",
                    "ingredients": ingredients_clean,
                }
            }
        )

        print(f"✅ set_recipe_ingredients: Set {len(ingredients)} ingredients")
        return {"success": True, "message": f"Set {len(ingredients)} ingredients"}
    except Exception as e:
        print(f"❌ set_recipe_ingredients error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def set_recipe_steps(
    session_id: str,
    steps: List[str],
) -> dict:
    """
    Set the complete cooking steps for the meal planner recipe.

    This REPLACES the entire steps list. To add or modify steps,
    send the full updated list including existing items.

    Args:
        steps: Complete list of cooking step instructions (just strings, no step numbers)
        session_id: Session ID (auto-injected)

    Example:
        set_recipe_steps([
            "Boil pasta in salted water for 10 minutes",
            "Meanwhile, mix eggs with grated parmesan cheese",
            "Drain pasta and immediately combine with egg mixture",
            "Serve hot with black pepper"
        ])
    """
    print(f"🔧 MCP TOOL: set_recipe_steps({len(steps)} steps, session={session_id})")

    try:
        await redis_client.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_steps",
                    "steps": steps,
                }
            }
        )

        print(f"✅ set_recipe_steps: Set {len(steps)} steps")
        return {"success": True, "message": f"Set {len(steps)} steps"}
    except Exception as e:
        print(f"❌ set_recipe_steps error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def save_recipe(
    name: str,
    ingredients: List[str],
    steps: List[dict],
    session_id: str,
    description: Optional[str] = None,
    total_time_minutes: Optional[int] = None,
    difficulty: Optional[str] = "medium",
    servings: Optional[int] = 4,
    tags: Optional[List[str]] = None
) -> dict:
    """
    Save a complete recipe to the database with structured data.

    Use this after having a conversation with the user where they described a recipe.
    Extract the structured information from the conversation before calling this.

    Args:
        name: Recipe name (e.g., "Spaghetti Carbonara")
        ingredients: List of ingredient strings (e.g., ["200g pasta", "100g bacon", "2 eggs"])
        steps: List of step dicts with 'instruction' and optional 'duration_minutes' and 'ingredients'
               Example: [{"instruction": "Boil pasta", "duration_minutes": 10}, ...]
        session_id: The meal planner session ID where this recipe was created
        description: Optional recipe description or story
        total_time_minutes: Total time to prepare and cook
        difficulty: Recipe difficulty: "easy", "medium", or "hard"
        servings: Number of servings
        tags: Optional list of tags (e.g., ["italian", "pasta", "quick"])

    Returns:
        dict: Success status, recipe ID, full recipe data for UI display, and message

    Example:
        save_recipe(
            name="Spaghetti Carbonara",
            ingredients=["200g spaghetti", "100g bacon", "2 eggs"],
            steps=[
                {"instruction": "Boil pasta for 10 minutes", "duration_minutes": 10},
                {"instruction": "Fry bacon until crispy", "duration_minutes": 5}
            ],
            difficulty="easy",
            total_time_minutes=20
        )
    """
    print(f"🔧 MCP TOOL: save_recipe(name='{name}', session_id='{session_id}')")

    try:
        api_url = os.getenv("API_URL", "http://raimy-api:8000")

        # Build recipe data
        recipe_data_obj = {
            "name": name,
            "description": description or f"A delicious {name} recipe created during a conversation.",
            "ingredients": ingredients,
            "steps": steps,
            "total_time_minutes": total_time_minutes,
            "difficulty": difficulty,
            "servings": servings,
            "tags": tags or ["ai-created", "meal-planner"],
            "meal_planner_session_id": session_id  # Link to conversation
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
                    print(f"✅ save_recipe: Recipe '{name}' saved with ID {recipe_id}")

                    # Return full recipe data for creating a structured message
                    return {
                        "success": True,
                        "recipe_id": recipe_id,
                        "message": f"Recipe '{name}' saved successfully!",
                        "recipe": recipe_data_obj | {"recipe_id": recipe_id}  # Merge recipe_id into data
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', 'Unknown error')
                    print(f"❌ save_recipe failed: {error_msg}")
                    return {
                        "success": False,
                        "message": f"Failed to save recipe: {error_msg}"
                    }
    except Exception as e:
        print(f"❌ save_recipe error: {str(e)}")
        return {"success": False, "message": f"Error saving recipe: {str(e)}"}


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
