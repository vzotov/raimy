"""
Kitchen Agent for Active Cooking Guidance

This agent specializes in guiding users through cooking recipes step-by-step,
managing ingredients, and setting timers.

Includes step state tracking to prevent duplicate tool calls within a single step.
"""
import logging
from typing import List, Optional, Dict, TypedDict

from langchain_core.messages import ToolMessage

from .base_agent import BaseAgent, AgentState


logger = logging.getLogger(__name__)


class KitchenStepState(TypedDict):
    """State for tracking the current cooking step"""
    index: int                           # Current step index (0-based)
    instruction: str                     # Step instruction text
    ingredients: List[str]               # Ingredients for this step
    duration_minutes: Optional[int]      # Timer duration if needed
    tools_to_call: List[str]             # Tools that should be called
    tools_called: List[str]              # Tools already called this step


class KitchenAgentState(AgentState):
    """Extended state for kitchen mode with step tracking"""
    current_step: Optional[KitchenStepState]


class KitchenAgent(BaseAgent):
    """Agent for active kitchen cooking guidance with step tracking"""

    # Tools that should only be called once per step
    DEDUPE_TOOLS = {"update_ingredients", "set_timer"}

    def _get_tool_status_message(self, tool_name: str) -> str:
        """
        Get user-friendly status message for kitchen tool execution

        Args:
            tool_name: Name of the tool being executed

        Returns:
            User-friendly status message
        """
        status_messages = {
            "set_ingredients": "gathering ingredients",
            "update_ingredients": "updating ingredients",
            "set_timer": "setting timer",
            "set_session_name": "preparing recipe"
        }
        return status_messages.get(tool_name, "thinking")

    def _should_skip_tool(self, tool_name: str, current_step: Optional[KitchenStepState]) -> bool:
        """
        Check if tool should be skipped (already called for this step)

        Args:
            tool_name: Name of the tool to check
            current_step: Current step state

        Returns:
            True if tool should be skipped, False otherwise
        """
        if not current_step:
            return False
        if tool_name not in self.DEDUPE_TOOLS:
            return False
        return tool_name in current_step.get("tools_called", [])

    async def _execute_tools_node(self, state: KitchenAgentState) -> Dict:
        """
        Execute tool calls from the LLM response with step-aware deduplication

        Args:
            state: Current agent state (includes current_step)

        Returns:
            Updated state with tool results and updated current_step
        """
        last_message = state["messages"][-1]
        tool_results = []

        # Get current step state
        current_step = state.get("current_step") or {}
        tools_called = list(current_step.get("tools_called", []))

        # Execute each tool call
        if hasattr(last_message, "tool_calls"):
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")

                logger.debug(f"🔧 Tool call: {tool_name}, args: {tool_args}")

                # Check if tool should be skipped (already called for this step)
                if self._should_skip_tool(tool_name, current_step):
                    logger.info(f"⏭️ Skipping {tool_name} - already called for step {current_step.get('index')}")
                    tool_results.append(ToolMessage(
                        content='{"success":true,"message":"Already called for this step"}',
                        tool_call_id=tool_id,
                        name=tool_name
                    ))
                    continue

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
                if "session_id" in state:
                    tool_args["session_id"] = state["session_id"]

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

                        # Track that we called this tool for deduplication
                        if tool_name in self.DEDUPE_TOOLS:
                            tools_called.append(tool_name)

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

        # Update current_step with new tools_called
        updated_step = {**current_step, "tools_called": tools_called} if current_step else None

        return {
            "messages": tool_results,
            "current_step": updated_step
        }

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        system_prompt: str,
        session_id: str,
        current_step: Optional[KitchenStepState] = None
    ) -> dict:
        """
        Run the agent with streaming support and step tracking

        Publishes LLM tokens to Redis as they arrive, accumulating content for final DB save.
        Includes current_step state for tool deduplication within a cooking step.

        Args:
            message: User message to process
            message_history: Previous message history from database
            system_prompt: System prompt for the agent
            session_id: Session ID for context
            current_step: Current cooking step state for deduplication

        Returns:
            dict with 'response' (str) and optional 'structured_outputs' (list)
        """
        import uuid
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

        # Convert message history to LangChain format
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

        # Add new user message
        langchain_messages.append(HumanMessage(content=message))

        # Create initial state with current_step for kitchen mode
        initial_state: KitchenAgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "has_generated_text": False,
            "current_step": current_step  # Kitchen-specific: step tracking
        }

        # Accumulators for final response
        accumulated_content = []
        saved_recipes = []
        all_messages = []

        # Generate unique message ID for this streaming response
        message_id = f"msg-{uuid.uuid4()}"

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

                    # Publish immediately for faster TTFT
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

        # Extract structured outputs
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
            "message_id": message_id
        }
