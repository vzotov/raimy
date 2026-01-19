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

    # Class attributes for tool tracking - override in subclasses
    TRACKED_TOOLS: Dict[str, str] = {}  # tool_name -> state_key mapping

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

    def _should_skip_tool(self, tool_name: str, tool_id: str, state: AgentState) -> Optional[ToolMessage]:
        """
        Check if tool should be skipped. Override in subclass for deduplication.

        Args:
            tool_name: Name of the tool
            tool_id: Tool call ID
            state: Current agent state

        Returns:
            ToolMessage if tool should be skipped, None otherwise
        """
        return None

    def _on_tool_executed(self, tool_name: str, state: AgentState, state_updates: Dict) -> None:
        """
        Called after successful tool execution. Override for custom tracking.
        Default implementation handles TRACKED_TOOLS class attribute.

        Args:
            tool_name: Name of the executed tool
            state: Current agent state
            state_updates: Dict to add state updates to
        """
        if tool_name in self.TRACKED_TOOLS:
            state_key = self.TRACKED_TOOLS[tool_name]
            state_updates[state_key] = True
            logger.info(f"📝 Tool tracked: {state_key} = True")

    def _finalize_state_updates(self, state: AgentState, state_updates: Dict) -> Dict:
        """
        Finalize state updates before returning. Override for custom state handling.

        Args:
            state: Current agent state
            state_updates: Accumulated state updates

        Returns:
            Final state updates dict to merge with return value
        """
        return state_updates

    async def _execute_tools_node(self, state: AgentState) -> Dict:
        """
        Execute tool calls from the LLM response.
        Uses hooks for customization: _should_skip_tool, _on_tool_executed, _finalize_state_updates

        Args:
            state: Current agent state

        Returns:
            Updated state with tool results and any state updates from hooks
        """
        last_message = state["messages"][-1]
        tool_results = []
        state_updates = {}

        if hasattr(last_message, "tool_calls"):
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")

                logger.debug(f"🔧 Tool call: {tool_name}, args: {tool_args}")

                # Hook: Check if tool should be skipped (for deduplication)
                skip_message = self._should_skip_tool(tool_name, tool_id, state)
                if skip_message:
                    tool_results.append(skip_message)
                    continue

                # Publish status
                status_message = self._get_tool_status_message(tool_name)
                try:
                    await self.redis_client.send_system_message(
                        state['session_id'],
                        "thinking",
                        status_message
                    )
                except Exception as e:
                    logger.warning(f"❌ Failed to publish tool status (non-fatal): {e}")

                # Override session_id with actual session from state
                if "session_id" in state:
                    tool_args["session_id"] = state["session_id"]

                # Find and execute the tool
                tool = next((t for t in self.mcp_tools if t.name == tool_name), None)

                if tool:
                    try:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append(ToolMessage(
                            content=str(result),
                            tool_call_id=tool_id,
                            name=tool_name
                        ))
                        # Hook: Post-execution tracking
                        self._on_tool_executed(tool_name, state, state_updates)

                    except Exception as e:
                        tool_results.append(ToolMessage(
                            content=f"Error executing {tool_name}: {str(e)}",
                            tool_call_id=tool_id,
                            name=tool_name
                        ))
                else:
                    tool_results.append(ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_id,
                        name=tool_name
                    ))

        # Hook: Finalize state updates
        final_updates = self._finalize_state_updates(state, state_updates)
        return {"messages": tool_results, **final_updates}

    # ========================================================================
    # Template Method Pattern for run_streaming
    # ========================================================================
    # The following methods implement a template method pattern that allows
    # subclasses to customize streaming behavior without duplicating the
    # core streaming logic.

    def _convert_message_history(self, message_history: List[Dict]) -> List[BaseMessage]:
        """
        Convert message history to LangChain format.
        Shared implementation for all agents.

        Args:
            message_history: Previous message history from database

        Returns:
            List of LangChain BaseMessage objects
        """
        def extract_text_content(content):
            """Extract plain text from message content (handles both string and structured formats)"""
            if isinstance(content, dict):
                if content.get("type") == "text":
                    return content.get("content", "")
                return ""
            return content

        langchain_messages = []
        for msg in message_history:
            text_content = extract_text_content(msg["content"])
            if text_content:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=text_content))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=text_content))

        return langchain_messages

    def _create_initial_state(
        self,
        messages: List[BaseMessage],
        session_id: str,
        system_prompt: str,
        **extra_state
    ) -> AgentState:
        """
        Create initial state for the graph. Override to add extra fields.

        Args:
            messages: LangChain messages including new user message
            session_id: Session ID for context
            system_prompt: System prompt for the agent
            **extra_state: Additional state fields from subclass

        Returns:
            Initial state dict for the graph
        """
        return {
            "messages": messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "has_generated_text": False
        }

    def _create_streaming_context(self) -> Dict:
        """
        Create context dict for accumulating data during streaming.
        Override to add extra tracking fields.

        Returns:
            Context dict with at least 'accumulated_content' and 'message_id'
        """
        return {
            "accumulated_content": [],
            "message_id": f"msg-{uuid.uuid4()}"
        }

    def _handle_tool_message(self, msg: ToolMessage, context: Dict) -> None:
        """
        Handle tool messages during streaming. Override for agent-specific logic.
        Default implementation does nothing.

        Args:
            msg: The ToolMessage from the graph
            context: Streaming context dict to update
        """
        pass

    def _build_response(self, context: Dict) -> dict:
        """
        Build final response dict. Override to add extra fields.

        Args:
            context: Streaming context dict with accumulated data

        Returns:
            Response dict with at least 'response' and 'message_id'
        """
        final_text = "".join(context["accumulated_content"])
        return {
            "response": final_text or "I apologize, I couldn't generate a response.",
            "message_id": context["message_id"]
        }

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        system_prompt: str,
        session_id: str,
        **extra_state
    ) -> dict:
        """
        Run the agent with streaming support.

        Uses template method pattern with hooks for customization:
        - _convert_message_history: Convert message history to LangChain format
        - _create_initial_state: Create initial state (override to add fields)
        - _create_streaming_context: Create streaming context (override to add tracking)
        - _handle_tool_message: Handle tool messages (override for custom logic)
        - _build_response: Build final response (override to add fields)

        Args:
            message: User message to process
            message_history: Previous message history from database
            system_prompt: System prompt for the agent
            session_id: Session ID for context
            **extra_state: Additional state fields for subclasses

        Returns:
            dict with 'response' (str) and 'message_id' (str), plus subclass-specific fields
        """
        # 1. Convert message history (shared)
        langchain_messages = self._convert_message_history(message_history)
        langchain_messages.append(HumanMessage(content=message))

        # 2. Create initial state (hook)
        initial_state = self._create_initial_state(
            langchain_messages, session_id, system_prompt, **extra_state
        )

        # 3. Setup streaming context (hook)
        context = self._create_streaming_context()

        # 4. Stream through the graph (shared)
        async for msg, metadata in self.graph.astream(
            initial_state,
            stream_mode="messages"
        ):
            node_name = metadata.get("langgraph_node", "")

            # 5. Handle LLM tokens (shared)
            if node_name == "call_llm" and isinstance(msg, AIMessage):
                if msg.content:
                    context["accumulated_content"].append(msg.content)
                    full_text_so_far = "".join(context["accumulated_content"])
                    try:
                        await self.redis_client.send_agent_text_message(
                            session_id,
                            full_text_so_far,
                            context["message_id"]
                        )
                    except Exception as e:
                        logger.warning(f"❌ Redis publish failed (non-fatal): {e}")

            # 6. Handle tool messages (hook)
            elif node_name == "execute_tools" and isinstance(msg, ToolMessage):
                self._handle_tool_message(msg, context)

        # 7. Send completion signal (shared)
        try:
            await self.redis_client.send_system_message(session_id, "thinking", None)
        except Exception as e:
            logger.warning(f"❌ Failed to publish completion signal (non-fatal): {e}")

        # 8. Build response (hook)
        return self._build_response(context)
