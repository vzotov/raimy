from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import asyncio

from database_service import database_service, RecipeModel, RecipeStepModel
from .models import RecipeNameRequest, SaveRecipeRequest
from auth_client import get_current_user

# Import broadcast_event from main API
broadcast_event = None

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.post("/name")
async def send_recipe_name(recipe: RecipeNameRequest):
    """Send recipe name to the client via SSE"""
    recipe_data = {
        "recipe_name": recipe.recipe_name,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Broadcast recipe name event
    if broadcast_event:
        await broadcast_event("recipe_name", recipe_data)
    
    return {"message": f"Recipe name sent: {recipe.recipe_name}"}


@router.post("/ingredients")
async def set_ingredients(ingredients_request: dict):
    """Send ingredients list to the client via SSE"""
    action = ingredients_request.get("action", "set")  # Default to "set" for backward compatibility
    ingredients_data = {
        "ingredients": ingredients_request.get("ingredients", []),
        "action": action,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Broadcast ingredients event
    if broadcast_event:
        await broadcast_event("ingredients", ingredients_data)
    
    action_text = "set" if action == "set" else "updated"
    return {"message": f"Ingredients {action_text}: {len(ingredients_data['ingredients'])} items"}


@router.get("/")
async def get_recipes(user_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get recipes from PostgreSQL database"""
    try:
        # Get all recipes for now (showing agent-created recipes)
        # TODO: Add proper user filtering if needed
        recipes = await database_service.get_recipes()

        return {
            "recipes": recipes,
            "count": len(recipes),
            "note": "Showing all recipes from PostgreSQL database."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recipes: {str(e)}")


@router.post("/")
async def save_recipe(recipe_request: SaveRecipeRequest, current_user: dict = Depends(get_current_user)):
    """Save a new recipe for the current user"""
    try:
        # Convert steps to RecipeStepModel objects
        steps = []
        for i, step_data in enumerate(recipe_request.steps):
            step = RecipeStepModel(
                step_number=i + 1,
                instruction=step_data.get("instruction", ""),
                duration_minutes=step_data.get("duration_minutes"),
                ingredients=step_data.get("ingredients")
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
            user_id=current_user["email"]  # Always use current user
        )

        # Save to PostgreSQL
        recipe_id = await database_service.save_recipe(recipe)

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