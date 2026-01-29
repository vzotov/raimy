"""
Agent Factory

Simple factory for creating agents based on session type.
"""
import logging
from typing import Dict, Union

from .kitchen.agent import KitchenAgent
from .recipe_creator.agent import RecipeCreatorAgent

logger = logging.getLogger(__name__)

DEFAULT_AGENT_TYPE = "recipe-creator"

# Cache of agent instances by session type
_agent_instances: Dict[str, Union[KitchenAgent, RecipeCreatorAgent]] = {}


async def get_agent(session_type: str = "recipe-creator") -> Union[KitchenAgent, RecipeCreatorAgent]:
    """
    Get or create a cached agent instance for the specified session type.

    Args:
        session_type: Session type ("kitchen" or "recipe-creator")

    Returns:
        Agent instance (cached or newly created)
    """
    global _agent_instances

    # Normalize unknown session types
    if session_type not in ("kitchen", "recipe-creator"):
        logger.warning(
            f"⚠️  Unknown session_type '{session_type}', defaulting to '{DEFAULT_AGENT_TYPE}'"
        )
        session_type = DEFAULT_AGENT_TYPE

    # Return cached instance if exists
    if session_type in _agent_instances:
        return _agent_instances[session_type]

    # Create new instance
    logger.info(f"🔄 Creating new agent instance for session_type='{session_type}'")

    if session_type == "kitchen":
        agent = KitchenAgent()
    else:
        agent = RecipeCreatorAgent()

    logger.info(f"✅ Created {agent.__class__.__name__} for '{session_type}'")

    _agent_instances[session_type] = agent
    return agent


def clear_agent_cache():
    """Clear the agent instance cache (useful for testing)"""
    global _agent_instances
    _agent_instances = {}
    logger.info("🧹 Agent cache cleared")