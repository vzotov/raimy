from fastapi import APIRouter, HTTPException, Depends
import os

import httpx

from ..services import database_service, RecipeModel, RecipeStepModel
from .models import SaveRecipeRequest
from core.auth_client import auth_client
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

async def get_current_user_with_storage(request: Request):
    """Get current user and ensure user data is stored in database"""
    try:
        # Verify authentication (pure auth check)
        auth_data = await auth_client.verify_auth(request)

        if not auth_data.get("authenticated"):
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = auth_data.get("user", {})

        # Store/update user data in database (app layer responsibility)
        if user_data and user_data.get('email'):
            try:
                await database_service.save_user(user_data)
                logger.debug(f"Updated user data for: {user_data.get('email')}")
            except Exception as e:
                logger.warning(f"Failed to store user data: {str(e)}")  # Don't fail auth for storage issues

        return user_data

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication error")

# Import broadcast_event from main API
broadcast_event = None

router = APIRouter(prefix="/api/recipes", tags=["recipes"])




@router.get("/")
async def get_recipes(current_user: dict = Depends(get_current_user_with_storage)):
    """Get recipes for the current user from PostgreSQL database"""
    try:
        logger.info(f"Getting recipes for user: {current_user['email']}")
        recipes = await database_service.get_recipes_by_user(current_user["email"])

        return {
            "recipes": recipes,
            "count": len(recipes),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recipes: {str(e)}")


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str, current_user: dict = Depends(get_current_user_with_storage)):
    """Get a single recipe by ID"""
    try:
        recipe = await database_service.get_recipe_by_id(recipe_id)

        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Verify ownership
        if recipe["user_id"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return {"recipe": recipe}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe {recipe_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get recipe: {str(e)}")


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str, current_user: dict = Depends(get_current_user_with_storage)):
    """Delete a recipe by ID"""
    try:
        # Get recipe to verify ownership
        recipe = await database_service.get_recipe_by_id(recipe_id)

        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Verify ownership
        if recipe["user_id"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete the recipe
        success = await database_service.delete_recipe(recipe_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete recipe")

        return {"message": "Recipe deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")


@router.post("/")
async def save_recipe(recipe_request: SaveRecipeRequest, current_user: dict = Depends(get_current_user_with_storage)):
    """Save a new recipe for the current user"""
    try:
        # Convert steps to RecipeStepModel objects
        steps = []
        for i, step_data in enumerate(recipe_request.steps):
            step = RecipeStepModel(
                instruction=step_data.get("instruction", ""),
                duration=step_data.get("duration"),
            )
            steps.append(step)

        # Create RecipeModel object with current user
        recipe = RecipeModel(
            name=recipe_request.name,
            description=recipe_request.description,
            ingredients=recipe_request.ingredients,
            steps=steps,
            total_time_minutes=recipe_request.total_time_minutes,
            difficulty=recipe_request.difficulty,
            servings=recipe_request.servings,
            tags=recipe_request.tags,
            user_id=current_user["email"],  # Always use current user
            chat_session_id=recipe_request.chat_session_id  # Link to session
        )

        logger.info(f"Saving recipe for user: {current_user['email']} with session ID: {recipe_request.chat_session_id}")

        # Save to PostgreSQL
        recipe_id = await database_service.save_recipe(recipe)

        # Update session's recipe_id FK to link saved recipe
        if recipe_request.chat_session_id:
            await database_service.update_session_recipe_id(
                session_id=recipe_request.chat_session_id,
                recipe_id=recipe_id
            )

        return {
            "message": "Recipe saved successfully",
            "recipe_id": recipe_id,
            "recipe": recipe.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


@router.post("/{recipe_id}/instacart-link")
async def generate_instacart_link(
    recipe_id: str,
    current_user: dict = Depends(get_current_user_with_storage)
):
    """
    Generate an Instacart shopping link for a recipe's ingredients.

    Calls the Instacart Developer Platform API to create a pre-populated
    shopping cart with all recipe ingredients. Caches the link for future requests.
    """
    # Check if Instacart API is configured
    instacart_api_key = os.getenv("INSTACART_API_KEY")
    if not instacart_api_key:
        raise HTTPException(
            status_code=503,
            detail="Instacart integration is not configured"
        )

    # Get recipe and verify ownership
    recipe = await database_service.get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Return cached link if available
    if recipe.get("instacart_link_url"):
        logger.info(f"Returning cached Instacart link for recipe {recipe_id}")
        return {"products_link_url": recipe["instacart_link_url"]}

    # Transform ingredients to Instacart format
    instacart_ingredients = []
    for ingredient in recipe.get("ingredients", []):
        # Use eng_name for Instacart search if available, fall back to name
        search_name = ingredient.get("eng_name") or ingredient.get("name", "")
        line_item = {
            "name": search_name,
            "display_text": _format_display_text(ingredient)
        }

        # Add measurements if amount/unit available
        if ingredient.get("amount"):
            measurement = {"quantity": _parse_quantity(ingredient["amount"])}
            if ingredient.get("unit"):
                measurement["unit"] = ingredient["unit"]
            line_item["measurements"] = [measurement]

        instacart_ingredients.append(line_item)

    # Build Instacart API request
    instacart_payload = {
        "title": recipe["name"],
        "ingredients": instacart_ingredients,
    }

    # Add optional fields if available
    if recipe.get("servings"):
        instacart_payload["servings"] = recipe["servings"]
    if recipe.get("total_time_minutes"):
        instacart_payload["cooking_time"] = recipe["total_time_minutes"]

    # Get Instacart API base URL from env var
    instacart_base_url = os.getenv(
        "INSTACART_API_URL",
        "https://connect.dev.instacart.tools"
    )
    instacart_api_url = f"{instacart_base_url}/idp/v1/products/recipe"

    # Call Instacart API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                instacart_api_url,
                headers={
                    "Authorization": f"Bearer {instacart_api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=instacart_payload
            )

            if response.status_code == 200:
                data = response.json()
                products_link_url = data["products_link_url"]

                # Cache the link in the database
                await database_service.update_recipe_instacart_link(
                    recipe_id, products_link_url
                )

                return {"products_link_url": products_link_url}
            else:
                logger.error(
                    f"Instacart API error: {response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=502,
                    detail="Failed to generate Instacart link"
                )

    except httpx.RequestError as e:
        logger.error(f"Instacart API connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Instacart"
        )


def _format_display_text(ingredient: dict) -> str:
    """Format ingredient for display in Instacart cart"""
    parts = []
    if ingredient.get("amount"):
        parts.append(str(ingredient["amount"]))
    if ingredient.get("unit"):
        parts.append(ingredient["unit"])
    parts.append(ingredient.get("name", ""))
    if ingredient.get("notes"):
        parts.append(f"({ingredient['notes']})")
    return " ".join(parts)


def _parse_quantity(amount) -> float:
    """Parse amount string to numeric quantity"""
    if isinstance(amount, (int, float)):
        return float(amount)
    try:
        amount_str = str(amount)
        # Handle fractions like "1/2"
        if "/" in amount_str:
            parts = amount_str.split("/")
            return float(parts[0]) / float(parts[1])
        return float(amount_str)
    except (ValueError, ZeroDivisionError):
        return 1.0  # Default to 1 if parsing fails


def create_recipes_router(broadcast_func):
    """Create recipes router with injected broadcast function"""
    global broadcast_event
    broadcast_event = broadcast_func
    return router
