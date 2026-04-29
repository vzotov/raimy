"""
Agent Factory

Returns the single UnifiedAgent for all session types.
"""
import logging
from typing import Dict

from .unified.agent import UnifiedAgent

logger = logging.getLogger(__name__)

_agent_instances: Dict[str, UnifiedAgent] = {}


async def get_agent(session_type: str = "chat") -> UnifiedAgent:
    """
    Get or create the cached UnifiedAgent instance.

    Args:
        session_type: Ignored — always returns UnifiedAgent

    Returns:
        UnifiedAgent instance (singleton)
    """
    global _agent_instances

    if "default" not in _agent_instances:
        logger.info("🔄 Creating UnifiedAgent")
        _agent_instances["default"] = UnifiedAgent()
        logger.info("✅ UnifiedAgent created")

    return _agent_instances["default"]


def clear_agent_cache():
    """Clear the agent instance cache (useful for testing)"""
    global _agent_instances
    _agent_instances = {}
    logger.info("🧹 Agent cache cleared")
