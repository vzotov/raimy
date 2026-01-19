"""
Recipe Creator Agent for Recipe Creation and Meal Planning

This agent specializes in helping users create recipes through conversation,
setting up recipe metadata, ingredients, and steps.

Includes state tracking for recipe components (metadata, ingredients, steps).
"""
import ast
import logging
from typing import List, Dict

from langchain_core.messages import BaseMessage, ToolMessage

from .base_agent import BaseAgent, AgentState


logger = logging.getLogger(__name__)


class RecipeCreatorState(AgentState):
    """Extended state for recipe creation with component tracking"""
    metadata_set: bool      # Has set_recipe_metadata been called
    ingredients_set: bool   # Has set_recipe_ingredients been called
    steps_set: bool         # Has set_recipe_steps been called


class RecipeCreatorAgent(BaseAgent):
    """Agent for recipe creation and meal planning"""

    # Tools that update recipe component tracking (handled by base class)
    TRACKED_TOOLS = {
        "set_recipe_metadata": "metadata_set",
        "set_recipe_ingredients": "ingredients_set",
        "set_recipe_steps": "steps_set",
    }

    def _get_tool_status_message(self, tool_name: str) -> str:
        """Get user-friendly status message for recipe creator tool execution"""
        status_messages = {
            "set_recipe_metadata": "setting up recipe",
            "set_recipe_ingredients": "adding ingredients",
            "set_recipe_steps": "writing steps",
            "save_recipe": "saving recipe",
            "generate_session_name": "naming session"
        }
        return status_messages.get(tool_name, "thinking")

    # ========================================================================
    # Template Method Hooks
    # ========================================================================

    def _create_initial_state(
        self,
        messages: List[BaseMessage],
        session_id: str,
        system_prompt: str,
        **extra_state
    ) -> RecipeCreatorState:
        """Create initial state with recipe tracking fields"""
        base_state = super()._create_initial_state(messages, session_id, system_prompt)
        return {
            **base_state,
            "metadata_set": extra_state.get("metadata_set", False),
            "ingredients_set": extra_state.get("ingredients_set", False),
            "steps_set": extra_state.get("steps_set", False),
        }

    def _create_streaming_context(self) -> Dict:
        """Create context with recipe-specific tracking"""
        context = super()._create_streaming_context()
        context["saved_recipes"] = []
        context["tracking"] = {
            "metadata_set": False,
            "ingredients_set": False,
            "steps_set": False,
        }
        return context

    def _handle_tool_message(self, msg: ToolMessage, context: Dict) -> None:
        """Track recipe tools and extract saved recipes"""
        # Track recipe component tools
        if msg.name in self.TRACKED_TOOLS:
            state_key = self.TRACKED_TOOLS[msg.name]
            context["tracking"][state_key] = True

        # Extract saved recipes
        if msg.name == "save_recipe" and "recipe" in str(msg.content):
            try:
                tool_result = ast.literal_eval(msg.content)
                if tool_result.get("success") and "recipe" in tool_result:
                    context["saved_recipes"].append(tool_result["recipe"])
            except Exception as e:
                logger.error(f"Error parsing save_recipe result: {e}")

    def _build_response(self, context: Dict) -> dict:
        """Build response with tracking flags and structured outputs"""
        base_response = super()._build_response(context)
        return {
            **base_response,
            "structured_outputs": context["saved_recipes"],
            **context["tracking"],
        }
