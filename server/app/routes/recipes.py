from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import asyncio

from ..services import database_service, RecipeModel, RecipeStepModel
from .models import RecipeNameRequest, SaveRecipeRequest
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


# Old HTTP-based routing endpoints removed - now using Redis PubSub
# MCP tools publish directly to Redis, API WebSocket subscribes to Redis


@router.get("/")
async def get_recipes(user_id: Optional[str] = None, current_user: dict = Depends(get_current_user_with_storage)):
    """Get recipes from PostgreSQL database"""
    try:
        # Get all recipes for now (showing agent-created recipes)
        # TODO: Add proper user filtering if needed
        logger.info(f"Getting recipes for user: {current_user['email']} with user_id param: {user_id}")
        recipes = await database_service.get_recipes()

        return {
            "recipes": recipes,
            "count": len(recipes),
            "note": "Showing all recipes from PostgreSQL database."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recipes: {str(e)}")


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
            meal_planner_session_id=recipe_request.meal_planner_session_id  # Link to session
        )

        logger.info(f"Saving recipe for user: {current_user['email']} with session ID: {recipe_request.meal_planner_session_id}")

        # Save to PostgreSQL
        recipe_id = await database_service.save_recipe(recipe)

        # Update session's recipe_id FK to link saved recipe
        if recipe_request.meal_planner_session_id:
            await database_service.update_session_recipe_id(
                session_id=recipe_request.meal_planner_session_id,
                recipe_id=recipe_id
            )

        return {
            "message": "Recipe saved successfully",
            "recipe_id": recipe_id,
            "recipe": recipe.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


def create_recipes_router(broadcast_func):
    """Create recipes router with injected broadcast function"""
    global broadcast_event
    broadcast_event = broadcast_func
    return router 