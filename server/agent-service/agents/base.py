"""
Base Agent Class for LangGraph-based Agents

Provides abstract base class with shared functionality for tool calling,
streaming, and Redis communication.
"""
import os
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Annotated, TypedDict, Optional

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

# Import from shared server/core module
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State schema for the LangGraph agent"""

    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    system_prompt: str
    has_generated_text: bool  # Track if LLM has generated text output


@dataclass
class AgentResponse:
    """Response from agent execution"""

    text: str  # Message to send to user
    structured_outputs: List[Dict]  # Saved recipes, etc.
    message_id: str  # Unique message ID


class BaseAgent(ABC):
    """Abstract base class for LangGraph-based chat agents with tool calling"""

    MODEL = "gpt-5-mini"

    def __init__(self, mcp_tools: Optional[List] = None):
        """
        Initialize the LangGraph agent.

        Args:
            mcp_tools: List of MCP tools converted to LangChain format
        """
        self.mcp_tools = mcp_tools or []
        self.llm = ChatOpenAI(
            model=self.MODEL,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        logger.info(f"🤖 Using OpenAI model: {self.MODEL}")

        # Bind tools to LLM with parallel tool calls enabled
        if self.mcp_tools:
            self.llm = self.llm.bind_tools(self.mcp_tools, parallel_tool_calls=True)

        self.graph = self._build_graph()
        self.redis_client = get_redis_client()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        workflow.add_node("call_llm", self._call_llm_node)

        if self.mcp_tools:
            workflow.add_node("execute_tools", self._execute_tools_node)
            workflow.add_conditional_edges(
                "call_llm",
                self._should_execute_tools,
                {"tools": "execute_tools", "end": END},
            )
            workflow.add_conditional_edges(
                "execute_tools",
                self._should_continue_after_tools,
                {"continue": "call_llm", "end": END},
            )
        else:
            workflow.add_edge("call_llm", END)

        workflow.set_entry_point("call_llm")
        return workflow.compile()

    async def _call_llm_node(self, state: AgentState) -> Dict:
        """Call the LLM to generate a response"""
        messages = [SystemMessage(content=state["system_prompt"])] + state["messages"]
        response = await self.llm.ainvoke(messages)
        has_text = bool(response.content and response.content.strip())
        return {"messages": [response], "has_generated_text": has_text}

    def _should_execute_tools(self, state: AgentState) -> str:
        """Determine if tools should be executed"""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    def _should_continue_after_tools(self, state: AgentState) -> str:
        """Determine if we should call LLM again after executing tools"""
        if state.get("has_generated_text", False):
            return "end"
        return "continue"

    @abstractmethod
    def _get_tool_status_message(self, tool_name: str) -> str:
        """
        Get user-friendly status message for a tool execution.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def build_system_prompt(self, session_data: Dict[str, Any]) -> str:
        """
        Build the system prompt for this agent.
        Must be implemented by subclasses.

        Args:
            session_data: Session data from database

        Returns:
            Complete system prompt string
        """
        pass

    async def _execute_tools_node(self, state: AgentState) -> Dict:
        """Execute tool calls from the LLM response"""
        last_message = state["messages"][-1]
        tool_results = []

        if not hasattr(last_message, "tool_calls"):
            return {"messages": tool_results}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")

            logger.debug(f"🔧 Tool call: {tool_name}")

            # Publish status message
            status_message = self._get_tool_status_message(tool_name)
            try:
                await self.redis_client.send_system_message(
                    state["session_id"], "thinking", status_message
                )
            except Exception as e:
                logger.warning(f"❌ Failed to publish tool status: {e}")

            # Inject session_id into tool args
            tool_args["session_id"] = state["session_id"]

            # Find and execute the tool
            tool = next((t for t in self.mcp_tools if t.name == tool_name), None)

            if tool:
                try:
                    result = await tool.ainvoke(tool_args)
                    tool_results.append(
                        ToolMessage(content=str(result), tool_call_id=tool_id, name=tool_name)
                    )
                except Exception as e:
                    tool_results.append(
                        ToolMessage(
                            content=f"Error executing {tool_name}: {str(e)}",
                            tool_call_id=tool_id,
                            name=tool_name,
                        )
                    )
            else:
                tool_results.append(
                    ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_id,
                        name=tool_name,
                    )
                )

        return {"messages": tool_results}

    def _extract_text_content(self, content: Any) -> str:
        """Extract plain text from message content (handles both string and structured formats)"""
        if isinstance(content, dict):
            if content.get("type") == "text":
                return content.get("content", "")
            return ""
        return content

    def _convert_message_history(self, message_history: List[Dict]) -> List[BaseMessage]:
        """Convert database message history to LangChain format"""
        langchain_messages = []
        for msg in message_history:
            text_content = self._extract_text_content(msg["content"])
            if text_content:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=text_content))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=text_content))
        return langchain_messages

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AgentResponse:
        """
        Run the agent with streaming support.

        Publishes LLM tokens to Redis as they arrive.

        Args:
            message: User message to process
            message_history: Previous message history from database
            session_id: Session ID for context
            session_data: Full session data for building system prompt

        Returns:
            AgentResponse with text, structured_outputs, and message_id
        """
        # Build system prompt using agent-specific logic
        system_prompt = self.build_system_prompt(session_data)

        # Convert message history and add new message
        langchain_messages = self._convert_message_history(message_history)
        langchain_messages.append(HumanMessage(content=message))

        # Create initial state
        initial_state: AgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "has_generated_text": False,
        }

        accumulated_content = []
        saved_recipes = []
        all_messages = []
        message_id = f"msg-{uuid.uuid4()}"

        # Stream through the graph
        async for msg, metadata in self.graph.astream(initial_state, stream_mode="messages"):
            all_messages.append(msg)
            node_name = metadata.get("langgraph_node", "")

            if node_name == "call_llm" and isinstance(msg, AIMessage):
                if msg.content:
                    accumulated_content.append(msg.content)
                    full_text_so_far = "".join(accumulated_content)
                    try:
                        await self.redis_client.send_agent_text_message(
                            session_id, full_text_so_far, message_id
                        )
                    except Exception as e:
                        logger.warning(f"❌ Redis publish failed: {e}")

        # Send completion signal
        try:
            await self.redis_client.send_system_message(session_id, "thinking", None)
        except Exception as e:
            logger.warning(f"❌ Failed to publish completion signal: {e}")

        # Extract structured outputs from tool messages
        for msg in all_messages:
            if isinstance(msg, ToolMessage):
                if msg.name == "save_recipe" and "recipe" in str(msg.content):
                    try:
                        import ast

                        tool_result = ast.literal_eval(msg.content)
                        if tool_result.get("success") and "recipe" in tool_result:
                            saved_recipes.append(tool_result["recipe"])
                    except Exception as e:
                        logger.error(f"Error parsing save_recipe result: {e}")

        final_text = "".join(accumulated_content)
        return AgentResponse(
            text=final_text or "I apologize, I couldn't generate a response.",
            structured_outputs=saved_recipes,
            message_id=message_id,
        )
