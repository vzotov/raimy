"""
Kitchen Agent for Active Cooking Guidance

This agent specializes in guiding users through cooking recipes step-by-step,
managing ingredients, and setting timers.

Includes step state tracking to prevent duplicate tool calls within a single step.
"""
import logging
from typing import List, Optional, Dict, TypedDict

from langchain_core.messages import BaseMessage, ToolMessage

from .base_agent import BaseAgent, AgentState


logger = logging.getLogger(__name__)


class KitchenStepState(TypedDict):
    """State for tracking the current cooking step"""
    index: int                           # Current step index (0-based)
    instruction: str                     # Step instruction text
    ingredients: List[str]               # Ingredients for this step
    duration_minutes: Optional[int]      # Timer duration if needed
    tools_to_call: List[str]             # Tools that should be called
    tools_called: List[str]              # Tools already called this step


class KitchenAgentState(AgentState):
    """Extended state for kitchen mode with step tracking"""
    current_step: Optional[KitchenStepState]


class KitchenAgent(BaseAgent):
    """Agent for active kitchen cooking guidance with step tracking"""

    # Tools that should only be called once per step
    DEDUPE_TOOLS = {"update_ingredients", "set_timer"}

    def _get_tool_status_message(self, tool_name: str) -> str:
        """Get user-friendly status message for kitchen tool execution"""
        status_messages = {
            "set_ingredients": "gathering ingredients",
            "update_ingredients": "updating ingredients",
            "set_timer": "setting timer",
            "set_session_name": "preparing recipe"
        }
        return status_messages.get(tool_name, "thinking")

    def _should_skip_tool(self, tool_name: str, tool_id: str, state: KitchenAgentState) -> Optional[ToolMessage]:
        """Check if tool should be skipped (already called for this step)"""
        current_step = state.get("current_step")
        if not current_step:
            return None
        if tool_name not in self.DEDUPE_TOOLS:
            return None
        if tool_name in current_step.get("tools_called", []):
            logger.info(f"⏭️ Skipping {tool_name} - already called for step {current_step.get('index')}")
            return ToolMessage(
                content='{"success":true,"message":"Already called for this step"}',
                tool_call_id=tool_id,
                name=tool_name
            )
        return None

    def _on_tool_executed(self, tool_name: str, state: KitchenAgentState, state_updates: Dict) -> None:
        """Track tools called for deduplication"""
        if tool_name in self.DEDUPE_TOOLS:
            # Store in state_updates for _finalize_state_updates to process
            if "_tools_called" not in state_updates:
                current_step = state.get("current_step") or {}
                state_updates["_tools_called"] = list(current_step.get("tools_called", []))
            state_updates["_tools_called"].append(tool_name)

    def _finalize_state_updates(self, state: KitchenAgentState, state_updates: Dict) -> Dict:
        """Update current_step with accumulated tools_called"""
        current_step = state.get("current_step") or {}
        tools_called = state_updates.pop("_tools_called", current_step.get("tools_called", []))

        if current_step:
            state_updates["current_step"] = {**current_step, "tools_called": tools_called}
        return state_updates

    # ========================================================================
    # Template Method Hooks
    # ========================================================================

    def _create_initial_state(
        self,
        messages: List[BaseMessage],
        session_id: str,
        system_prompt: str,
        **extra_state
    ) -> KitchenAgentState:
        """Create initial state with current_step for kitchen mode"""
        base_state = super()._create_initial_state(messages, session_id, system_prompt)
        return {
            **base_state,
            "current_step": extra_state.get("current_step"),
        }
