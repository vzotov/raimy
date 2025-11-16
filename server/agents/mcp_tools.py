"""
MCP to LangChain Tools Converter

This module fetches tools from the MCP server and converts them
to LangChain tool format for use with the LangGraph agent.
"""
import os
import httpx
from typing import List, Dict, Any, Optional, Callable
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field, create_model


async def fetch_mcp_tools(mcp_url: str) -> List[Dict[str, Any]]:
    """
    Fetch tools from MCP server via HTTP

    Args:
        mcp_url: URL of the MCP server

    Returns:
        List of tool definitions from MCP server
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # MCP HTTP protocol: POST to /mcp with list_tools request
            response = await client.post(
                mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
            )

            if response.status_code == 200:
                result = response.json()
                tools = result.get("result", {}).get("tools", [])
                print(f"✅ Fetched {len(tools)} tools from MCP server")
                return tools
            else:
                print(f"❌ Failed to fetch MCP tools: HTTP {response.status_code}")
                return []

    except Exception as e:
        print(f"❌ Error fetching MCP tools: {e}")
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
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    # Extract content from MCP response
                    content = result.get("result", {}).get("content", [])
                    if content and len(content) > 0:
                        return content[0].get("text", {})
                    return result.get("result", {})
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
            print(f"✅ Converted MCP tool: {tool_name}")

        except Exception as e:
            print(f"❌ Failed to convert tool {tool_name}: {e}")

    return langchain_tools


async def load_mcp_tools_for_langchain(
    mcp_url: Optional[str] = None
) -> List[StructuredTool]:
    """
    Load and convert MCP tools for use with LangChain

    Args:
        mcp_url: MCP server URL (defaults to environment variable)

    Returns:
        List of LangChain StructuredTool instances
    """
    if mcp_url is None:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-service:8002/mcp")

    print(f"🔄 Loading MCP tools from {mcp_url}")

    # Fetch tools from MCP server
    mcp_tools = await fetch_mcp_tools(mcp_url)

    if not mcp_tools:
        print("⚠️  No MCP tools loaded")
        return []

    # Convert to LangChain format
    langchain_tools = convert_mcp_tools_to_langchain(mcp_tools, mcp_url)

    print(f"✅ Loaded {len(langchain_tools)} LangChain tools from MCP")
    return langchain_tools
