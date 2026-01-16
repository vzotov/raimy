"""
Base Agent Class for LangGraph-based Agents

This module provides the abstract base class for all LangGraph-based agents,
containing shared functionality for tool calling, streaming, and Redis communication.
"""
import os
import sys
import logging
import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Annotated, TypedDict, Optional

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.redis_client import get_redis_client

# Initialize logger
logger = logging.getLogger(__name__)


# Define the state schema for the agent
class AgentState(TypedDict):
    """State schema for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    system_prompt: str
    has_generated_text: bool  # Track if LLM has generated text output


class BaseAgent(ABC):
    """Abstract base class for LangGraph-based chat agents with tool calling"""

    def __init__(self, mcp_tools: Optional[List] = None):
        """
        Initialize the LangGraph agent

        Args:
            mcp_tools: List of MCP tools converted to LangChain format
        """
        self.mcp_tools = mcp_tools or []

        # Model is configurable via environment variable
        model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info(f"🤖 Using OpenAI model: {model_name}")

        # Bind tools to LLM if available
        # Enable parallel_tool_calls to allow multiple tools in one response
        if self.mcp_tools:
            self.llm = self.llm.bind_tools(self.mcp_tools, parallel_tool_calls=True)

        # Build the graph
        self.graph = self._build_graph()

        # Initialize Redis client for streaming
        self.redis_client = get_redis_client()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("call_llm", self._call_llm_node)

        # Check if we have tools
        if self.mcp_tools:
            workflow.add_node("execute_tools", self._execute_tools_node)

            # Add conditional edges for tool calling
            workflow.add_conditional_edges(
                "call_llm",
                self._should_execute_tools,
                {
                    "tools": "execute_tools",
                    "end": END
                }
            )
            # After tools, decide whether to call LLM again or end
            # If text was already generated with the tools, we're done
            workflow.add_conditional_edges(
                "execute_tools",
                self._should_continue_after_tools,
                {
                    "continue": "call_llm",
                    "end": END
                }
            )
        else:
            # No tools, just end after LLM call
            workflow.add_edge("call_llm", END)

        # Set entry point
        workflow.set_entry_point("call_llm")

        return workflow.compile()

    async def _call_llm_node(self, state: AgentState) -> Dict:
        """
        Call the LLM to generate a response

        Args:
            state: Current agent state

        Returns:
            Updated state with LLM response
        """
        # Build messages with system prompt
        messages = [SystemMessage(content=state["system_prompt"])] + state["messages"]

        # Call LLM
        response = await self.llm.ainvoke(messages)

        # Check if response has text content (not just tool calls)
        has_text = bool(response.content and response.content.strip())

        # Return updated state
        return {
            "messages": [response],
            "has_generated_text": has_text  # Mark if we've generated text
        }

    def _should_execute_tools(self, state: AgentState) -> str:
        """
        Determine if tools should be executed

        Args:
            state: Current agent state

        Returns:
            "tools" if tools should be executed, "end" otherwise
        """
        last_message = state["messages"][-1]

        # Always execute tool calls if present, even if text was also generated
        # This handles parallel tool calls where model returns text + tools together
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # No tool calls - we're done
        return "end"

    def _should_continue_after_tools(self, state: AgentState) -> str:
        """
        Determine if we should call LLM again after executing tools

        Args:
            state: Current agent state

        Returns:
            "continue" to call LLM again, "end" to finish
        """
        # If we've already generated text output, don't call LLM again
        # This prevents unnecessary additional LLM calls after tools execute
        if state.get("has_generated_text", False):
            return "end"

        # No text generated yet, continue to LLM to get response
        return "continue"

    @abstractmethod
    def _get_tool_status_message(self, tool_name: str) -> str:
        """
        Get user-friendly status message for a tool execution.
        Must be implemented by subclasses.

        Args:
            tool_name: Name of the tool being executed

        Returns:
            User-friendly status message
        """
        pass

    async def _execute_tools_node(self, state: AgentState) -> Dict:
        """
        Execute tool calls from the LLM response

        Args:
            state: Current agent state

        Returns:
            Updated state with tool results
        """
        last_message = state["messages"][-1]
        tool_results = []

        # Execute each tool call
        if hasattr(last_message, "tool_calls"):
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")

                logger.debug(f"🔧 Tool call: {tool_name}, args before injection: {tool_args}")

                # Publish status based on tool name
                status_message = self._get_tool_status_message(tool_name)
                try:
                    await self.redis_client.send_system_message(
                        state['session_id'],
                        "thinking",
                        status_message
                    )
                except Exception as e:
                    logger.warning(f"❌ Failed to publish tool status (non-fatal): {e}")

                # Always override session_id with the actual session from state
                # The LLM might provide example values from tool docs, so we need to replace them
                if "session_id" in state:
                    original_session = tool_args.get("session_id", "not provided")
                    tool_args["session_id"] = state["session_id"]
                    logger.debug(f"✅ Overrode session_id: '{original_session}' → '{state['session_id']}'")

                # Find the tool in our tool list
                tool = next((t for t in self.mcp_tools if t.name == tool_name), None)

                if tool:
                    try:
                        # Execute the tool
                        result = await tool.ainvoke(tool_args)

                        # Create tool message with result
                        tool_message = ToolMessage(
                            content=str(result),
                            tool_call_id=tool_id,
                            name=tool_name
                        )
                        tool_results.append(tool_message)

                    except Exception as e:
                        # Create error message
                        error_message = ToolMessage(
                            content=f"Error executing {tool_name}: {str(e)}",
                            tool_call_id=tool_id,
                            name=tool_name
                        )
                        tool_results.append(error_message)
                else:
                    # Tool not found
                    error_message = ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    tool_results.append(error_message)

        return {"messages": tool_results}

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        system_prompt: str,
        session_id: str
    ) -> dict:
        """
        Run the agent with streaming support

        Publishes LLM tokens to Redis as they arrive, accumulating content for final DB save.

        Args:
            message: User message to process
            message_history: Previous message history from database
            system_prompt: System prompt for the agent
            session_id: Session ID for context

        Returns:
            dict with 'response' (str) and optional 'structured_outputs' (list)
        """
        # Convert message history to LangChain format
        # Helper to extract text content from structured message
        def extract_text_content(content):
            """Extract plain text from message content (handles both string and structured formats)"""
            if isinstance(content, dict):
                # Structured content: extract the actual text from TextContent
                if content.get("type") == "text":
                    return content.get("content", "")
                # For other types (recipe, ingredients), return empty string
                return ""
            # Plain string (backward compatibility)
            return content

        langchain_messages = []
        for msg in message_history:
            text_content = extract_text_content(msg["content"])
            if text_content:  # Only add if there's actual text content
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=text_content))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=text_content))

        # Add new user message
        langchain_messages.append(HumanMessage(content=message))

        # Create initial state
        initial_state: AgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "has_generated_text": False  # Reset for new turn
        }

        # Accumulators for final response
        accumulated_content = []
        saved_recipes = []
        all_messages = []

        # Generate unique message ID for this streaming response
        message_id = f"msg-{uuid.uuid4()}"

        # Track current node to send appropriate status messages
        current_node = None

        # Stream through the graph
        async for msg, metadata in self.graph.astream(
            initial_state,
            stream_mode="messages"
        ):
            # Track all messages for final processing
            all_messages.append(msg)

            # Get current node name
            node_name = metadata.get("langgraph_node", "")

            # Filter for LLM-generated content from call_llm node
            if node_name == "call_llm" and isinstance(msg, AIMessage):
                # Handle token streaming
                if msg.content:
                    # Accumulate for final save
                    accumulated_content.append(msg.content)

                    # Publish immediately for faster TTFT (time to first token)
                    # No buffering - users see content as soon as it arrives
                    full_text_so_far = "".join(accumulated_content)
                    try:
                        await self.redis_client.send_agent_text_message(
                            session_id,
                            full_text_so_far,
                            message_id
                        )
                    except Exception as e:
                        logger.warning(f"❌ Redis publish failed (non-fatal): {e}")

        # Send completion signal to clear thinking status
        try:
            await self.redis_client.send_system_message(
                session_id,
                "thinking",
                None
            )
        except Exception as e:
            logger.warning(f"❌ Failed to publish completion signal (non-fatal): {e}")

        # Combine accumulated content
        final_text = "".join(accumulated_content)

        # Extract structured outputs (same logic as current run method)
        for msg in all_messages:
            if isinstance(msg, ToolMessage):
                if msg.name == "save_recipe" and "recipe" in str(msg.content):
                    try:
                        import json
                        import ast
                        tool_result = ast.literal_eval(msg.content)
                        if tool_result.get("success") and "recipe" in tool_result:
                            saved_recipes.append(tool_result["recipe"])
                    except Exception as e:
                        logger.error(f"Error parsing save_recipe result: {e}")

        response_text = final_text or "I apologize, I couldn't generate a response."

        return {
            "response": response_text,
            "structured_outputs": saved_recipes,
            "message_id": message_id  # Return message ID for reference
        }
