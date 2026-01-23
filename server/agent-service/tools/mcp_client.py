"""
MCP Client Wrapper using langchain-mcp-adapters

Replaces the 366-line custom implementation with the official library.
Provides tool loading with session-type tag filtering.
"""
import os
import logging
import traceback
from typing import List, Optional

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

# Global client instance (reused across requests)
_mcp_client: Optional[MultiServerMCPClient] = None


def _get_mcp_client() -> MultiServerMCPClient:
    """Get or create the global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-service:8002/mcp")
        logger.info(f"🔄 Creating MCP client for {mcp_url}")

        _mcp_client = MultiServerMCPClient({
            "mcp": {
                "transport": "streamable_http",
                "url": mcp_url
            }
        })
    return _mcp_client


async def load_mcp_tools(session_type: Optional[str] = None) -> List[BaseTool]:
    """
    Load MCP tools and optionally filter by session type.

    Args:
        session_type: Optional session type to filter tools ("kitchen" or "recipe-creator")

    Returns:
        List of LangChain tools from MCP server, filtered by session_type if provided
    """
    logger.info(f"🔄 Loading MCP tools for session_type='{session_type}'")

    try:
        client = _get_mcp_client()
        all_tools = await client.get_tools()

        # Log available tools
        tool_names = [getattr(t, "name", "?") for t in all_tools]
        logger.info(f"📡 MCP server returned {len(all_tools)} tools: {tool_names}")

        if not session_type:
            logger.info(f"✅ Loaded {len(all_tools)} tools (no filtering)")
            return all_tools

        # Filter by session type tags
        filtered_tools = []
        for tool in all_tools:
            tool_name = getattr(tool, "name", "<unnamed>")

            # Get tags from metadata._meta._fastmcp.tags
            # TODO: Simplify once https://github.com/langchain-ai/langchain-mcp-adapters/issues/138 is implemented
            metadata = getattr(tool, "metadata", {}) or {}
            mcp_meta = metadata.get("_meta", {})
            fastmcp_meta = mcp_meta.get("_fastmcp", {})
            tool_tags = fastmcp_meta.get("tags", [])

            if session_type in tool_tags:
                filtered_tools.append(tool)
            else:
                logger.info(f"   Skipping '{tool_name}': tags={tool_tags}")

        if filtered_tools:
            matched_names = [getattr(t, "name", "?") for t in filtered_tools]
            logger.info(f"✅ Loaded {len(filtered_tools)} tools for '{session_type}': {matched_names}")
        else:
            logger.warning(f"⚠️  No tools matched session_type='{session_type}'")

        return filtered_tools

    except Exception as e:
        logger.error(f"❌ Error loading MCP tools: {e}")
        logger.error(traceback.format_exc())
        return []


async def close_mcp_client():
    """Close the MCP client connection"""
    global _mcp_client
    if _mcp_client is not None:
        try:
            await _mcp_client.close()
        except Exception as e:
            logger.warning(f"Error closing MCP client: {e}")
        _mcp_client = None
        logger.info("🔌 MCP client closed")
