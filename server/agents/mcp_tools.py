"""
MCP to LangChain Tools Converter

This module fetches tools from the MCP server and converts them
to LangChain tool format for use with the LangGraph agent.
"""
import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional, Callable
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field, create_model

# Initialize logger
logger = logging.getLogger(__name__)


async def fetch_mcp_tools(mcp_url: str, session_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch tools from MCP server via HTTP and filter by session_type tags

    Args:
        mcp_url: URL of the MCP server
        session_type: Optional session type to filter tools ("kitchen" or "recipe-creator")

    Returns:
        List of tool definitions from MCP server, filtered by session_type if provided
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # MCP HTTP protocol: POST to /mcp with list_tools request
            # FastMCP requires Accept header for both JSON and event-stream
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                },
                headers={
                    "Accept": "application/json, text/event-stream"
                }
            )

            if response.status_code == 200:
                # FastMCP returns SSE format - parse the event stream
                response_text = response.text

                # Extract JSON from SSE format: "event: message\ndata: {...}"
                if response_text.startswith("event: message"):
                    lines = response_text.split('\n')
                    for line in lines:
                        if line.startswith("data: "):
                            json_data = line[6:].strip()  # Remove "data: " prefix and whitespace
                            if json_data:
                                try:
                                    result = json.loads(json_data)
                                    tools = result.get("result", {}).get("tools", [])

                                    # Client-side filtering by session type
                                    if session_type:
                                        filtered_tools = []
                                        for tool in tools:
                                            # Tags are in _meta._fastmcp.tags for FastMCP tools
                                            tool_tags = tool.get("_meta", {}).get("_fastmcp", {}).get("tags", [])
                                            # Include tool if session_type is in the tool's tags
                                            if session_type in tool_tags:
                                                filtered_tools.append(tool)

                                        logger.info(f"✅ Filtered {len(tools)} tools → {len(filtered_tools)} for session_type='{session_type}'")
                                        return filtered_tools
                                    else:
                                        logger.info(f"✅ Fetched {len(tools)} tools from MCP server (no filtering)")
                                        return tools
                                except json.JSONDecodeError as e:
                                    logger.error(f"❌ JSON parse error: {e}")
                                    logger.error(f"   Data: {json_data[:100]}...")
                                    return []
                else:
                    # Try parsing as plain JSON (fallback)
                    try:
                        result = response.json()
                        tools = result.get("result", {}).get("tools", [])

                        # Client-side filtering by session type
                        if session_type:
                            filtered_tools = []
                            for tool in tools:
                                # Tags are in _meta._fastmcp.tags for FastMCP tools
                                tool_tags = tool.get("_meta", {}).get("_fastmcp", {}).get("tags", [])
                                # Include tool if session_type is in the tool's tags
                                if session_type in tool_tags:
                                    filtered_tools.append(tool)

                            logger.info(f"✅ Filtered {len(tools)} tools → {len(filtered_tools)} for session_type='{session_type}'")
                            return filtered_tools
                        else:
                            logger.info(f"✅ Fetched {len(tools)} tools from MCP server (no filtering)")
                            return tools
                    except Exception as e:
                        logger.error(f"❌ Could not parse as JSON: {e}")
                        logger.error(f"   Response: {response_text[:200]}...")
                        return []

                logger.error("❌ Could not parse MCP response")
                return []
            else:
                logger.error(f"❌ Failed to fetch MCP tools: HTTP {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"❌ Error fetching MCP tools: {e}")
        return []


def _create_tool_function(tool_name: str, mcp_url: str) -> Callable:
    """
    Create a function that calls the MCP tool via HTTP

    Args:
        tool_name: Name of the MCP tool
        mcp_url: URL of the MCP server

    Returns:
        Async function that calls the tool
    """
    async def tool_function(**kwargs) -> Dict[str, Any]:
        """Execute MCP tool via HTTP"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": kwargs
                        }
                    },
                    headers={
                        "Accept": "application/json, text/event-stream"
                    }
                )

                if response.status_code == 200:
                    # Parse SSE format response
                    response_text = response.text
                    result = None

                    if response_text.startswith("event: message"):
                        lines = response_text.split('\n')
                        for line in lines:
                            if line.startswith("data: "):
                                json_data = line[6:]
                                result = json.loads(json_data) if json_data else {}
                                break
                    else:
                        result = response.json()

                    if result:
                        # Extract content from MCP response
                        content = result.get("result", {}).get("content", [])
                        if content and len(content) > 0:
                            return content[0].get("text", {})
                        return result.get("result", {})

                    return {
                        "success": False,
                        "message": "Could not parse response"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    return tool_function


def _convert_mcp_schema_to_pydantic(
    tool_name: str,
    input_schema: Dict[str, Any]
) -> type[BaseModel]:
    """
    Convert MCP JSON schema to Pydantic model for LangChain

    Args:
        tool_name: Name of the tool
        input_schema: JSON schema from MCP tool

    Returns:
        Pydantic model class
    """
    properties = input_schema.get("properties", {})
    required_fields = input_schema.get("required", [])

    # Build field definitions for Pydantic model
    field_definitions = {}

    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type", "string")
        field_description = field_schema.get("description", "")

        # Map JSON schema types to Python types
        python_type = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List,
            "object": Dict
        }.get(field_type, str)

        # Handle array types
        if field_type == "array":
            items_type = field_schema.get("items", {}).get("type", "string")
            if items_type == "object":
                python_type = List[Dict]
            else:
                python_type = List[str]

        # Create field with description
        is_required = field_name in required_fields

        if is_required:
            field_definitions[field_name] = (
                python_type,
                Field(..., description=field_description)
            )
        else:
            field_definitions[field_name] = (
                Optional[python_type],
                Field(None, description=field_description)
            )

    # Create dynamic Pydantic model
    model_name = f"{tool_name.title().replace('_', '')}Input"
    return create_model(model_name, **field_definitions)


def convert_mcp_tools_to_langchain(
    mcp_tools: List[Dict[str, Any]],
    mcp_url: str
) -> List[StructuredTool]:
    """
    Convert MCP tools to LangChain StructuredTool format

    Args:
        mcp_tools: List of MCP tool definitions
        mcp_url: URL of the MCP server for tool execution

    Returns:
        List of LangChain StructuredTool instances
    """
    langchain_tools = []

    for mcp_tool in mcp_tools:
        tool_name = mcp_tool.get("name", "unknown")
        tool_description = mcp_tool.get("description", "")
        input_schema = mcp_tool.get("inputSchema", {})

        try:
            # Create Pydantic model for tool arguments
            args_schema = _convert_mcp_schema_to_pydantic(tool_name, input_schema)

            # Create function that calls MCP tool
            tool_function = _create_tool_function(tool_name, mcp_url)

            # Create LangChain StructuredTool
            langchain_tool = StructuredTool(
                name=tool_name,
                description=tool_description,
                func=tool_function,
                coroutine=tool_function,  # For async support
                args_schema=args_schema
            )

            langchain_tools.append(langchain_tool)
            logger.info(f"✅ Converted MCP tool: {tool_name}")

        except Exception as e:
            logger.error(f"❌ Failed to convert tool {tool_name}: {e}")

    return langchain_tools


async def load_mcp_tools_for_langchain(
    mcp_url: Optional[str] = None,
    session_type: Optional[str] = None
) -> List[StructuredTool]:
    """
    Load and convert MCP tools for use with LangChain, filtered by session type

    Args:
        mcp_url: MCP server URL (defaults to environment variable)
        session_type: Session type to filter tools ("kitchen" or "recipe-creator")

    Returns:
        List of LangChain StructuredTool instances
    """
    if mcp_url is None:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-service:8002/mcp")

    logger.info(f"🔄 Loading MCP tools from {mcp_url} for session_type='{session_type}'")

    # Fetch tools from MCP server with session_type filtering
    mcp_tools = await fetch_mcp_tools(mcp_url, session_type=session_type)

    if not mcp_tools:
        logger.warning("⚠️  No MCP tools loaded")
        return []

    # Convert to LangChain format
    langchain_tools = convert_mcp_tools_to_langchain(mcp_tools, mcp_url)

    logger.info(f"✅ Loaded {len(langchain_tools)} LangChain tools from MCP")
    return langchain_tools
