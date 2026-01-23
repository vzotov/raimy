"""
Recipe Creator Agent for Meal Planning and Recipe Creation

Specializes in helping users create recipes through conversation,
setting up recipe metadata, ingredients, and steps.
"""
from typing import Dict, Any

from ..base import BaseAgent
from .prompt import RECIPE_CREATOR_PROMPT


class RecipeCreatorAgent(BaseAgent):
    """Agent for recipe creation and meal planning"""

    def _get_tool_status_message(self, tool_name: str) -> str:
        """Get user-friendly status message for recipe creator tool execution"""
        status_messages = {
            "set_recipe_metadata": "setting up recipe",
            "set_recipe_ingredients": "adding ingredients",
            "set_recipe_steps": "writing steps",
            "set_recipe_nutrition": "calculating nutrition",
            "save_recipe": "saving recipe",
            "generate_session_name": "naming session",
        }
        return status_messages.get(tool_name, "thinking")

    def build_system_prompt(self, session_data: Dict[str, Any]) -> str:
        """
        Build system prompt for recipe creator mode.

        Args:
            session_data: Session data (not used for recipe creator)

        Returns:
            Recipe creator system prompt
        """
        return RECIPE_CREATOR_PROMPT
