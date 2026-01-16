"""
Kitchen Agent for Active Cooking Guidance

This agent specializes in guiding users through cooking recipes step-by-step,
managing ingredients, and setting timers.
"""
from typing import List, Optional

from .base_agent import BaseAgent


class KitchenAgent(BaseAgent):
    """Agent for active kitchen cooking guidance"""

    def _get_tool_status_message(self, tool_name: str) -> str:
        """
        Get user-friendly status message for kitchen tool execution

        Args:
            tool_name: Name of the tool being executed

        Returns:
            User-friendly status message
        """
        status_messages = {
            "set_ingredients": "gathering ingredients",
            "update_ingredients": "updating ingredients",
            "set_timer": "setting timer",
            "set_session_name": "preparing recipe"
        }
        return status_messages.get(tool_name, "thinking")
