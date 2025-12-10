from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime


class TimerRequest(BaseModel):
    """Request model for setting cooking timers"""
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "duration": 300,
            "label": "Boil pasta"
        }]
    })

    duration: int = Field(..., description="Timer duration in seconds")
    label: str = Field(..., description="Timer label/description")


class RecipeNameRequest(BaseModel):
    """Request model for sending recipe names via SSE"""
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "recipe_name": "Spaghetti Carbonara"
        }]
    })

    recipe_name: str = Field(..., description="Name of the recipe")


class SaveRecipeRequest(BaseModel):
    """Request model for saving new recipes"""
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "name": "Spaghetti Carbonara",
            "description": "Classic Italian pasta dish",
            "ingredients": ["pasta", "eggs", "bacon", "cheese"],
            "steps": [
                {"instruction": "Boil pasta", "duration": 10},
                {"instruction": "Cook bacon", "duration": 5}
            ],
            "total_time_minutes": 30,
            "difficulty": "Easy",
            "servings": 4,
            "tags": ["Italian", "Pasta", "Quick"]
        }]
    })

    name: str = Field(..., description="Recipe name")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: List[str] = Field(..., description="List of ingredients")
    steps: List[dict] = Field(..., description="List of cooking steps")
    total_time_minutes: Optional[int] = Field(None, description="Total cooking time in minutes")
    difficulty: Optional[str] = Field(None, description="Recipe difficulty level")
    servings: Optional[int] = Field(None, description="Number of servings")
    tags: Optional[List[str]] = Field(None, description="Recipe tags")
    user_id: Optional[str] = Field(None, description="User ID (auto-filled from session)")
    meal_planner_session_id: Optional[str] = Field(None, description="Meal planner session ID where this recipe was created")


class CreateSessionRequest(BaseModel):
    """Request model for creating a meal planner session"""
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "session_type": "meal-planner"
        }]
    })

    session_type: Optional[str] = Field("meal-planner", description="Session type: 'meal-planner' or 'kitchen'")
    recipe_id: Optional[str] = Field(None, description="Optional recipe ID to associate with the session")


class UpdateSessionNameRequest(BaseModel):
    """Request model for updating meal planner session name"""
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "session_name": "Thai Curry Recipe"
        }]
    })

    session_name: str = Field(..., description="New session name") 