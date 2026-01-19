"""
Recipe Creator Agent for Recipe Creation and Meal Planning

This agent specializes in helping users create recipes through conversation,
setting up recipe metadata, ingredients, and steps.
"""
from typing import List, Optional

from .base_agent import BaseAgent


class RecipeCreatorAgent(BaseAgent):
    """Agent for recipe creation and meal planning"""

    def _get_tool_status_message(self, tool_name: str) -> str:
        """
        Get user-friendly status message for recipe creator tool execution

        Args:
            tool_name: Name of the tool being executed

        Returns:
            User-friendly status message
        """
        status_messages = {
            "set_recipe_metadata": "setting up recipe",
            "set_recipe_ingredients": "adding ingredients",
            "set_recipe_steps": "writing steps",
            "save_recipe": "saving recipe",
            "generate_session_name": "naming session"
        }
        return status_messages.get(tool_name, "thinking")
