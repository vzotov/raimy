from pydantic import BaseModel, Field
from typing import List, Optional


class TimerRequest(BaseModel):
    """Request model for setting cooking timers"""
    duration: int = Field(..., description="Timer duration in seconds", example=300)
    label: str = Field(..., description="Timer label/description", example="Boil pasta")


class RecipeNameRequest(BaseModel):
    """Request model for sending recipe names via SSE"""
    recipe_name: str = Field(..., description="Name of the recipe", example="Spaghetti Carbonara")


class SaveRecipeRequest(BaseModel):
    """Request model for saving new recipes"""
    name: str = Field(..., description="Recipe name", example="Spaghetti Carbonara")
    description: Optional[str] = Field(None, description="Recipe description", example="Classic Italian pasta dish")
    ingredients: List[str] = Field(..., description="List of ingredients", example=["pasta", "eggs", "bacon", "cheese"])
    steps: List[dict] = Field(..., description="List of cooking steps", example=[
        {"instruction": "Boil pasta", "duration_minutes": 10, "ingredients": ["pasta"]},
        {"instruction": "Cook bacon", "duration_minutes": 5, "ingredients": ["bacon"]}
    ])
    total_time_minutes: Optional[int] = Field(None, description="Total cooking time in minutes", example=30)
    difficulty: Optional[str] = Field(None, description="Recipe difficulty level", example="Easy")
    servings: Optional[int] = Field(None, description="Number of servings", example=4)
    tags: Optional[List[str]] = Field(None, description="Recipe tags", example=["Italian", "Pasta", "Quick"])
    user_id: Optional[str] = Field(None, description="User ID (auto-filled from session)") 