"""
Kitchen Agent for Active Cooking Guidance

Specializes in guiding users through cooking recipes step-by-step,
managing ingredients, and setting timers.

Includes step state tracking to prevent duplicate tool calls within a single step.
"""
import uuid
import logging
from typing import List, Dict, Any, Optional, TypedDict

from langchain_core.messages import AIMessage, ToolMessage

from ..base import BaseAgent, AgentState, AgentResponse
from .prompt import KITCHEN_PROMPT

logger = logging.getLogger(__name__)


class KitchenStepState(TypedDict):
    """State for tracking the current cooking step"""

    index: int  # Current step index (0-based)
    instruction: str  # Step instruction text
    ingredients: List[str]  # Ingredients for this step
    duration_minutes: Optional[int]  # Timer duration if needed
    tools_to_call: List[str]  # Tools that should be called
    tools_called: List[str]  # Tools already called this step


class KitchenAgentState(AgentState):
    """Extended state for kitchen mode with step tracking"""

    current_step: Optional[KitchenStepState]


class KitchenAgent(BaseAgent):
    """Agent for active kitchen cooking guidance with step tracking"""

    # Tools that should only be called once per step
    DEDUPE_TOOLS = {"update_ingredients", "set_timer"}

    def _get_tool_status_message(self, tool_name: str) -> str:
        """Get user-friendly status message for kitchen tool execution"""
        status_messages = {
            "set_ingredients": "gathering ingredients",
            "update_ingredients": "updating ingredients",
            "set_timer": "setting timer",
            "set_session_name": "preparing recipe",
        }
        return status_messages.get(tool_name, "thinking")

    def build_system_prompt(self, session_data: Dict[str, Any]) -> str:
        """
        Build system prompt with recipe context for kitchen mode.

        Args:
            session_data: Session data containing recipe and ingredients

        Returns:
            Complete system prompt with recipe context injected
        """
        system_prompt = KITCHEN_PROMPT

        # Add recipe context if available
        recipe_data = session_data.get("recipe")
        if recipe_data:
            recipe_context = self._format_recipe_context(recipe_data)
            system_prompt = system_prompt + "\n\n" + recipe_context

        # Add current ingredients state if resuming session
        ingredients = session_data.get("ingredients", [])
        if ingredients:
            ingredient_context = self._format_ingredient_context(ingredients)
            system_prompt = system_prompt + ingredient_context

        return system_prompt

    def _format_recipe_context(self, recipe_data: Dict[str, Any]) -> str:
        """Format recipe data for system prompt injection"""
        recipe_name = recipe_data.get("name", "Unknown Recipe")
        description = recipe_data.get("description", "")
        ingredients = recipe_data.get("ingredients", [])
        steps = recipe_data.get("steps", [])

        context = f"""
────────────────────────────────────────
RECIPE TO COOK: {recipe_name}
────────────────────────────────────────

The user has selected this recipe to cook. Guide them through it step-by-step.

**Recipe Name:** {recipe_name}
"""
        if description:
            context += f"**Description:** {description}\n"

        context += "\n**Ingredients:**\n"
        for ing in ingredients:
            name = ing.get("name", "")
            amount = ing.get("amount", "")
            unit = ing.get("unit", "")
            notes = ing.get("notes", "")

            ing_line = f"- {name}"
            if amount:
                ing_line = f"- {amount} {unit} {name}" if unit else f"- {amount} {name}"
            if notes:
                ing_line += f" ({notes})"
            context += ing_line + "\n"

        context += "\n**Cooking Steps (guide through ONE step at a time):**\n"
        for i, step in enumerate(steps, 1):
            instruction = step.get("instruction", "")
            duration = step.get("duration")

            context += f"{i}. {instruction}"
            if duration:
                context += f" [TIMER: {duration} minutes]"
            context += "\n"

        context += """
────────────────────────────────────────
INSTRUCTIONS:
────────────────────────────────────────
⚠️  IMPORTANT: The session name and ingredients are ALREADY SET in the database.
   DO NOT call set_session_name() or set_ingredients() - this data is already saved.

🔴 CRITICAL: ONE response = ONE update_ingredients call + text instruction TOGETHER

**When user says "done", "next", or confirms completion:**
Your response MUST contain BOTH in ONE message:
1. ONE update_ingredients call that does BOTH:
   - Mark previous step's ingredients: highlighted=false, used=true
   - Highlight current step's ingredients: highlighted=true
2. Your spoken instruction text for the current step

❌ WRONG: Tool call only (no text) → then another response with text + tool
✅ CORRECT: Tool call + text instruction in SAME response

**Timer rules:**
- For passive cooking steps (bake, simmer, rest, chill), use set_timer() tool
- Include set_timer in the SAME response as update_ingredients and text

**Critical rules:**
- NEVER make a tool-only response without text
- NEVER call update_ingredients twice in one turn
- After your instruction, STOP and wait for user to respond

**General rules:**
- Do NOT mention duration in your text - just state the instruction
- Do NOT add meta-commentary like "Great, step X is done"
- Just give the next instruction directly

Start with ONLY the first step, then STOP.
"""
        return context

    def _format_ingredient_context(self, ingredients: List[Dict]) -> str:
        """Format current ingredient state for prompt context"""
        context = "\n\n**CURRENT SESSION STATE:**\n"
        context += f"Ingredients for this recipe ({len(ingredients)} total):\n"
        for ing in ingredients:
            status = ""
            if ing.get("used"):
                status = " [USED]"
            elif ing.get("highlighted"):
                status = " [CURRENTLY USING]"
            context += f"- {ing['name']}: {ing.get('amount', '')} {ing.get('unit', '')}{status}\n"
        context += "\nContinue guiding from where the session left off.\n"
        return context

    def _calculate_current_step(
        self, recipe: Dict[str, Any], ingredients: List[Dict]
    ) -> Optional[KitchenStepState]:
        """
        Calculate current step from recipe and ingredient state.

        Determines which step the user is on based on which ingredients have been used.

        Args:
            recipe: Recipe data with steps and ingredients
            ingredients: Current ingredient state from session

        Returns:
            Current step state dict or None if all steps complete
        """
        if not recipe:
            return None

        steps = recipe.get("steps", [])
        recipe_ingredients = recipe.get("ingredients", [])

        if not steps:
            return None

        # Map ingredients to steps (simple text matching)
        step_ingredients: Dict[int, List[str]] = {}
        for i, step in enumerate(steps):
            instruction = step.get("instruction", "").lower()
            step_ingredients[i] = [
                ing.get("name", "")
                for ing in recipe_ingredients
                if ing.get("name", "").lower() in instruction
            ]

        # Find used ingredients from session state
        used = {ing.get("name", "") for ing in ingredients if ing.get("used")}

        # Find current step based on used ingredients
        for i, step in enumerate(steps):
            step_ings = set(step_ingredients.get(i, []))
            if not step_ings.issubset(used):
                # This step's ingredients not all used yet - this is current step
                tools_to_call = []
                if step_ingredients.get(i):
                    tools_to_call.append("update_ingredients")
                if step.get("duration"):
                    tools_to_call.append("set_timer")

                return {
                    "index": i,
                    "instruction": step.get("instruction", ""),
                    "ingredients": step_ingredients.get(i, []),
                    "duration_minutes": step.get("duration"),
                    "tools_to_call": tools_to_call,
                    "tools_called": [],
                }

        # All steps complete
        return None

    def _should_skip_tool(
        self, tool_name: str, current_step: Optional[KitchenStepState]
    ) -> bool:
        """Check if tool should be skipped (already called for this step)"""
        if not current_step:
            return False
        if tool_name not in self.DEDUPE_TOOLS:
            return False
        return tool_name in current_step.get("tools_called", [])

    async def _execute_tools_node(self, state: KitchenAgentState) -> Dict:
        """Execute tool calls with step-aware deduplication"""
        last_message = state["messages"][-1]
        tool_results = []

        # Get current step state
        current_step = state.get("current_step") or {}
        tools_called = list(current_step.get("tools_called", []))

        if not hasattr(last_message, "tool_calls"):
            return {"messages": tool_results}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")

            logger.debug(f"🔧 Tool call: {tool_name}")

            # Check if tool should be skipped (already called for this step)
            if self._should_skip_tool(tool_name, current_step):
                logger.info(
                    f"⏭️ Skipping {tool_name} - already called for step {current_step.get('index')}"
                )
                tool_results.append(
                    ToolMessage(
                        content='{"success":true,"message":"Already called for this step"}',
                        tool_call_id=tool_id,
                        name=tool_name,
                    )
                )
                continue

            # Publish status message
            status_message = self._get_tool_status_message(tool_name)
            try:
                await self.redis_client.send_system_message(
                    state["session_id"], "thinking", status_message
                )
            except Exception as e:
                logger.warning(f"❌ Failed to publish tool status: {e}")

            # Inject session_id
            tool_args["session_id"] = state["session_id"]

            # Find and execute the tool
            tool = next((t for t in self.mcp_tools if t.name == tool_name), None)

            if tool:
                try:
                    result = await tool.ainvoke(tool_args)
                    tool_results.append(
                        ToolMessage(
                            content=str(result), tool_call_id=tool_id, name=tool_name
                        )
                    )
                    # Track that we called this tool for deduplication
                    if tool_name in self.DEDUPE_TOOLS:
                        tools_called.append(tool_name)
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

        # Update current_step with new tools_called
        updated_step = (
            {**current_step, "tools_called": tools_called} if current_step else None
        )

        return {"messages": tool_results, "current_step": updated_step}

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AgentResponse:
        """
        Run the agent with streaming support and step tracking.

        Args:
            message: User message to process
            message_history: Previous message history from database
            session_id: Session ID for context
            session_data: Full session data

        Returns:
            AgentResponse with text, structured_outputs, and message_id
        """
        # Build system prompt
        system_prompt = self.build_system_prompt(session_data)

        # Convert message history
        langchain_messages = self._convert_message_history(message_history)
        langchain_messages.append(
            __import__("langchain_core.messages", fromlist=["HumanMessage"]).HumanMessage(
                content=message
            )
        )

        # Calculate current step for tool deduplication
        recipe_data = session_data.get("recipe")
        ingredients = session_data.get("ingredients", [])
        current_step = None
        if recipe_data:
            current_step = self._calculate_current_step(recipe_data, ingredients)
            if current_step:
                logger.debug(
                    f"📍 Current step: {current_step.get('index')} - {current_step.get('instruction')[:50]}..."
                )

        # Create initial state with current_step for kitchen mode
        initial_state: KitchenAgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "has_generated_text": False,
            "current_step": current_step,
        }

        accumulated_content = []
        saved_recipes = []
        all_messages = []
        message_id = f"msg-{uuid.uuid4()}"

        # Stream through the graph
        async for msg, metadata in self.graph.astream(
            initial_state, stream_mode="messages"
        ):
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

        final_text = "".join(accumulated_content)
        return AgentResponse(
            text=final_text or "I apologize, I couldn't generate a response.",
            structured_outputs=saved_recipes,
            message_id=message_id,
        )
