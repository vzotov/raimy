"""Pydantic schemas for structured LLM outputs in unified agent"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class UnifiedIntentSchema(BaseModel):
    """Analysis of user's message to determine intent"""

    intent: Literal[
        "create_recipe",     # user wants a new recipe
        "modify_recipe",     # user wants to change existing recipe
        "start_cooking",     # user wants to start cooking current recipe
        "next_step",         # advance to next cooking step
        "previous_step",     # go back a step
        "set_timer",         # set a cooking timer
        "save_recipe",       # save current recipe to library
        "buy_ingredients",   # shopping list
        "generate_images",   # generate step images for current recipe
        "answer_question",   # cooking/food Q&A
        "general_chat",      # anything else
    ] = Field(
        description=(
            "What the user wants: "
            "'create_recipe' to create a new recipe, "
            "'modify_recipe' to change the existing recipe, "
            "'start_cooking' to begin cooking from step 1, "
            "'next_step' to move to next step, "
            "'previous_step' to go back, "
            "'set_timer' for timer requests, "
            "'save_recipe' to save recipe to library, "
            "'buy_ingredients' for shopping list, "
            "'generate_images' to create step images, "
            "'answer_question' for cooking Q&A, "
            "'general_chat' for other messages"
        )
    )
    recipe_request: Optional[str] = Field(
        default=None,
        description="Extracted recipe request if intent=create_recipe (e.g., 'spaghetti carbonara')",
    )
    modification_request: Optional[str] = Field(
        default=None,
        description="What to change if intent=modify_recipe (e.g., 'make it vegetarian')",
    )
    question: Optional[str] = Field(
        default=None,
        description="Extracted question if intent=answer_question",
    )
    timer_minutes: Optional[int] = Field(
        default=None,
        description="Timer duration in minutes if intent=set_timer",
    )
    timer_label: Optional[str] = Field(
        default=None,
        description="Timer label if intent=set_timer (e.g., 'boil pasta')",
    )


class UnifiedStepGuidanceSchema(BaseModel):
    """Response for step guidance with inline-bolded ingredients"""

    spoken_response: str = Field(
        description=(
            "Natural spoken instruction for this step (concise, 1-2 sentences). "
            "MUST bold all ingredient names and quantities inline using **markdown bold**. "
            "Example: 'Add **200g of spaghetti** to the boiling water and cook for **8 minutes**.'"
        )
    )
    next_step_prompt: str = Field(
        description="Short phrase user would say when done (e.g., 'It's sizzling', 'All mixed', 'Ready to flip')"
    )
    suggested_timer_minutes: Optional[int] = Field(
        default=None,
        description="Timer minutes ONLY for passive cooking (boiling, baking, simmering). None for active tasks.",
    )
    timer_label: Optional[str] = Field(
        default=None,
        description="Timer label if suggesting a timer (plain text)",
    )
