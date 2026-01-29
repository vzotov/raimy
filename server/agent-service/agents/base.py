"""
Base Agent Interface

Defines the required API for agents in the agent service.
All agents must inherit from BaseAgent and their events from AgentEvent.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List


@dataclass
class AgentEvent:
    """
    Base event class for all agent events.

    All agent-specific events must inherit from this class.
    The `type` field should be a Literal type in subclasses to define allowed event types.

    Common event types (subclasses may add more):
    - "thinking": Processing indicator (data: str message)
    - "text": Text response (data: {"content": str, "message_id": str})
    - "complete": Generation finished (data: None)
    """

    type: str
    data: Any


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    All agents must inherit from this class and implement:
    - generate_greeting(): For new session greetings
    - run_streaming(): For processing user messages

    Example:
        class MyAgent(BaseAgent):
            async def generate_greeting(self, **kwargs) -> str:
                return "Hello!"

            async def run_streaming(
                self,
                message: str,
                message_history: List[Dict],
                session_id: str,
                session_data: Dict[str, Any],
            ) -> AsyncGenerator[MyAgentEvent, None]:
                yield MyAgentEvent(type="text", data={"content": "Hi"})
                yield MyAgentEvent(type="complete", data=None)
    """

    @abstractmethod
    async def generate_greeting(self, **kwargs) -> str:
        """
        Generate a greeting for new sessions.

        Args:
            **kwargs: Agent-specific arguments (e.g., recipe_name for KitchenAgent)

        Returns:
            Greeting message string
        """
        pass

    @abstractmethod
    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Process a user message and yield events.

        Args:
            message: User message text
            message_history: Previous messages from database
            session_id: Session identifier
            session_data: Full session data including recipe, agent_state, etc.

        Yields:
            AgentEvent (or subclass) for each step of processing
        """
        yield  # Required for async generator type hint
