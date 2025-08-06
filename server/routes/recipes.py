from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import asyncio

from firebase_service import firebase_service, Recipe, RecipeStep
from .models import RecipeNameRequest, SaveRecipeRequest
from routes.auth import get_current_user_flexible

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


@router.get("/")
async def get_recipes(user_id: Optional[str] = None, current_user: dict = Depends(get_current_user_flexible)):
    """Get recipes from the database, filtered by current user"""
    try:
        # Always filter by current user for security
        recipes = await firebase_service.get_recipes_by_user(current_user["email"])
        
        return {
            "recipes": recipes,
            "count": len(recipes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recipes: {str(e)}")


@router.post("/")
async def save_recipe(recipe_request: SaveRecipeRequest, current_user: dict = Depends(get_current_user_flexible)):
    """Save a new recipe for the current user"""
    try:
        # Convert steps to RecipeStep objects
        steps = []
        for i, step_data in enumerate(recipe_request.steps):
            step = RecipeStep(
                step_number=i + 1,
                instruction=step_data.get("instruction", ""),
                duration_minutes=step_data.get("duration_minutes"),
                ingredients=step_data.get("ingredients")
            )
            steps.append(step)
        
        # Create Recipe object with current user
        recipe = Recipe(
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
        
        # Save to Firebase
        recipe_id = await firebase_service.save_recipe(recipe)
        
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