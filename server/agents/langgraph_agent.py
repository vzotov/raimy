"""
LangGraph-based Agent for Chat Assistance

This module implements a stateful agent using LangGraph for processing
chat messages with tool calling capabilities.
"""
import os
from typing import List, Dict, Annotated, TypedDict, Optional
from typing_extensions import TypedDict as TypedDictExt

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI


# Define the state schema for the agent
class AgentState(TypedDict):
    """State schema for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    system_prompt: str


class LangGraphAgent:
    """LangGraph-based chat agent with tool calling"""

    def __init__(self, mcp_tools: Optional[List] = None):
        """
        Initialize the LangGraph agent

        Args:
            mcp_tools: List of MCP tools converted to LangChain format
        """
        self.mcp_tools = mcp_tools or []
        self.llm = ChatOpenAI(
            model="gpt-5-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Bind tools to LLM if available
        if self.mcp_tools:
            self.llm = self.llm.bind_tools(self.mcp_tools)

        # Build the graph
        self.graph = self._build_graph()

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
            workflow.add_edge("execute_tools", "call_llm")
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

        # Return updated state
        return {"messages": [response]}

    def _should_execute_tools(self, state: AgentState) -> str:
        """
        Determine if tools should be executed

        Args:
            state: Current agent state

        Returns:
            "tools" if tools should be executed, "end" otherwise
        """
        last_message = state["messages"][-1]

        # Check if the last message has tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

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

                print(f"🔧 Tool call: {tool_name}, args before injection: {tool_args}")

                # Always override session_id with the actual session from state
                # The LLM might provide example values from tool docs, so we need to replace them
                if "session_id" in state:
                    original_session = tool_args.get("session_id", "not provided")
                    tool_args["session_id"] = state["session_id"]
                    print(f"✅ Overrode session_id: '{original_session}' → '{state['session_id']}'")

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

    async def run(
        self,
        message: str,
        message_history: List[Dict],
        system_prompt: str,
        session_id: str
    ) -> dict:
        """
        Run the agent to process a message

        Args:
            message: User message to process
            message_history: Previous message history from database
            system_prompt: System prompt for the agent
            session_id: Session ID for context

        Returns:
            dict with 'response' (str) and optional 'structured_outputs' (list)
        """
        # Convert message history to LangChain format
        langchain_messages = []
        for msg in message_history:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        # Add new user message
        langchain_messages.append(HumanMessage(content=message))

        # Create initial state
        initial_state: AgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "system_prompt": system_prompt
        }

        # Run the graph
        result = await self.graph.ainvoke(initial_state)

        # Extract the last AI message and check for tool results
        final_messages = result["messages"]
        ai_response = None
        saved_recipes = []

        # Scan messages for AI response and tool results
        for msg in final_messages:
            if isinstance(msg, AIMessage):
                ai_response = msg.content
            elif isinstance(msg, ToolMessage):
                # Check if this is a save_recipe tool result
                if msg.name == "save_recipe" and "recipe" in str(msg.content):
                    try:
                        # Parse the tool result (it's a string representation of dict)
                        import json
                        import ast
                        tool_result = ast.literal_eval(msg.content)
                        if tool_result.get("success") and "recipe" in tool_result:
                            saved_recipes.append(tool_result["recipe"])
                    except Exception as e:
                        print(f"Error parsing save_recipe result: {e}")

        response_text = ai_response or "I apologize, I couldn't generate a response."

        # Return response with any structured outputs
        return {
            "response": response_text,
            "structured_outputs": saved_recipes if saved_recipes else []
        }
