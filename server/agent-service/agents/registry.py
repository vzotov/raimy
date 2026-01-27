"""
Agent Factory

Simple factory for creating agents based on session type.
"""
import logging
from typing import Dict, Union

from .base import BaseAgent
from .kitchen.agent import KitchenAgent
from .recipe_creator.agent import RecipeCreatorAgent
from tools import load_mcp_tools

logger = logging.getLogger(__name__)

DEFAULT_AGENT_TYPE = "recipe-creator"

# Cache of agent instances by session type
_agent_instances: Dict[str, Union[BaseAgent, RecipeCreatorAgent]] = {}


async def get_agent(session_type: str = "recipe-creator") -> Union[BaseAgent, RecipeCreatorAgent]:
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
        mcp_tools = await load_mcp_tools(session_type=session_type)
        agent = KitchenAgent(mcp_tools=mcp_tools)
        logger.info(
            f"✅ Created {agent.__class__.__name__} for '{session_type}' with {len(mcp_tools)} tools"
        )
    else:
        # RecipeCreatorAgent uses structured outputs, no MCP tools
        agent = RecipeCreatorAgent()
        logger.info(
            f"✅ Created {agent.__class__.__name__} for '{session_type}' (structured outputs)"
        )

    _agent_instances[session_type] = agent
    return agent


def clear_agent_cache():
    """Clear the agent instance cache (useful for testing)"""
    global _agent_instances
    _agent_instances = {}
    logger.info("🧹 Agent cache cleared")