"""Pydantic schemas for structured LLM outputs in kitchen agent"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class KitchenIntentAnalysis(BaseModel):
    """Analysis of user's message to determine intent in kitchen context"""

    intent: Literal[
        "get_recipe",      # No recipe + user wants one
        "start_cooking",   # Recipe exists + "let's start"
        "next_step",       # "done", "next", "okay" - move forward
        "previous_step",   # "go back", "previous" - move back
        "ask_question",    # Question about current step/recipe
        "set_timer",       # Explicit timer request
        "general_chat",    # Other conversation
    ] = Field(
        description=(
            "What the user wants: "
            "'get_recipe' to create/find a recipe, "
            "'start_cooking' to begin from step 1, "
            "'next_step' to move to next step, "
            "'previous_step' to go back, "
            "'ask_question' for step-related questions, "
            "'set_timer' for timer requests, "
            "'general_chat' for other messages"
        )
    )
    recipe_request: Optional[str] = Field(
        default=None,
        description="Extracted recipe request if intent=get_recipe (e.g., 'spaghetti carbonara')",
    )
    question: Optional[str] = Field(
        default=None,
        description="Extracted question if intent=ask_question",
    )
    timer_minutes: Optional[int] = Field(
        default=None,
        description="Timer duration in minutes if intent=set_timer",
    )
    timer_label: Optional[str] = Field(
        default=None,
        description="Timer label if intent=set_timer (e.g., 'boil pasta')",
    )


class StepGuidanceResponse(BaseModel):
    """Response for step guidance including what to say and ingredients to highlight"""

    spoken_response: str = Field(
        description="Natural spoken instruction for this step (concise, 1-2 sentences)"
    )
    next_step_prompt: str = Field(
        description="Short phrase user would say when done (e.g., 'It's sizzling', 'All mixed', 'Ready to flip')"
    )
    ingredients_to_highlight: List[str] = Field(
        default_factory=list,
        description="Ingredient names EXACTLY as listed in recipe. Must match exactly for UI lookup."
    )
    ingredients_to_mark_used: List[str] = Field(
        default_factory=list,
        description="Ingredient names EXACTLY as listed in recipe, fully consumed. Must match exactly for UI lookup."
    )
    suggested_timer_minutes: Optional[int] = Field(
        default=None,
        description="Timer minutes ONLY for passive cooking (boiling, baking, simmering). None for active tasks."
    )
    timer_label: Optional[str] = Field(
        default=None,
        description="Timer label if suggesting a timer (plain text)"
    )


class QuestionResponse(BaseModel):
    """Response to a question about the current step or recipe"""

    answer: str = Field(
        description="Helpful answer to the user's question (concise, 1-3 sentences)"
    )
