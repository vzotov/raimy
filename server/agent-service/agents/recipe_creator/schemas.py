"""Pydantic schemas for structured LLM outputs in recipe creator agent"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class RequestAnalysis(BaseModel):
    """Analysis of user's request to determine intent"""

    intent: Literal["recipe", "modify", "suggest", "question"] = Field(
        description=(
            "What the user wants: "
            "'recipe' for NEW specific recipe, "
            "'modify' to change existing recipe, "
            "'suggest' for ideas/recommendations, "
            "'question' for clarification needed"
        )
    )
    recipe_request: Optional[str] = Field(
        default=None,
        description="Extracted recipe request if intent=recipe (e.g., 'spaghetti carbonara for 4 people')",
    )
    modification_request: Optional[str] = Field(
        default=None,
        description="What user wants to change if intent=modify (e.g., 'make it vegetarian', 'add more garlic')",
    )
    what_to_modify: Optional[List[Literal[
        "name", "description", "servings", "difficulty", "time", "tags",  # metadata fields
        "ingredients", "steps", "nutrition"  # content fields
    ]]] = Field(
        default=None,
        description="Which specific recipe fields need regeneration for modify intent. Only include fields that DIRECTLY need to change.",
    )
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="3 specific dish suggestions if intent=suggest",
    )
    text_response: Optional[str] = Field(
        default=None,
        description="Text response for question/suggest intents",
    )


class RecipeMetadata(BaseModel):
    """Recipe metadata - name, description, and basic info"""

    name: str = Field(description="Recipe name")
    description: str = Field(description="Brief 1-2 sentence description of the dish")
    difficulty: Literal["easy", "medium", "hard"] = Field(
        description="Difficulty level based on techniques and time required"
    )
    total_time_minutes: int = Field(description="Total cooking time in minutes")
    servings: int = Field(description="Number of servings")
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization (e.g., 'italian', 'quick', 'vegetarian')",
    )


class Ingredient(BaseModel):
    """Single ingredient with amount and unit"""

    name: str = Field(description="Ingredient name")
    amount: Optional[str] = Field(
        default=None, description="Amount (e.g., '2', '1/2', '3-4')"
    )
    unit: Optional[str] = Field(
        default=None, description="Unit (e.g., 'cups', 'tbsp', 'pieces')"
    )
    eng_name: Optional[str] = Field(
        default=None, description="English name for non-English recipes"
    )


class RecipeIngredients(BaseModel):
    """List of ingredients for a recipe"""

    ingredients: List[Ingredient] = Field(description="List of recipe ingredients")


class Step(BaseModel):
    """Single cooking step"""

    instruction: str = Field(description="Step instruction")
    duration_minutes: Optional[int] = Field(
        default=None, description="Estimated duration in minutes"
    )


class RecipeSteps(BaseModel):
    """List of cooking steps"""

    steps: List[Step] = Field(description="Ordered list of cooking steps")


class RecipeNutrition(BaseModel):
    """Estimated nutrition information for entire recipe"""

    calories: int = Field(description="Total calories")
    carbs: int = Field(description="Total carbohydrates in grams")
    fats: int = Field(description="Total fats in grams")
    proteins: int = Field(description="Total protein in grams")


class DishSuggestion(BaseModel):
    """A single dish suggestion"""

    name: str = Field(description="Dish name")
    description: str = Field(description="Brief 1-sentence description")


class DishSuggestions(BaseModel):
    """3 dish suggestions for the user"""

    suggestions: List[DishSuggestion] = Field(
        description="Exactly 3 specific dish suggestions",
        min_length=3,
        max_length=3,
    )
    response_text: str = Field(
        description="Friendly text introducing the suggestions"
    )
