"""
Kitchen Agent for Active Cooking Guidance

Specializes in guiding users through cooking recipes step-by-step,
managing ingredients, and setting timers.

Includes step state tracking to prevent duplicate tool calls within a single step.
Supports recipe generation via Redis subscription when no recipe exists.
"""
import asyncio
import json
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
    """Extended state for kitchen mode with step tracking and recipe generation"""

    current_step: Optional[KitchenStepState]
    recipe: Optional[Dict[str, Any]]  # Recipe object - same structure as DB-loaded
    recipe_generation_mode: bool  # True when generating recipe, False when guiding


class KitchenAgent(BaseAgent):
    """Agent for active kitchen cooking guidance with step tracking"""

    # Tools that should only be called once per step
    DEDUPE_TOOLS = {"update_ingredients", "set_timer"}

    # Recipe creation tools that trigger Redis subscription
    RECIPE_TOOLS = {
        "set_recipe_metadata",
        "set_recipe_ingredients",
        "set_recipe_steps",
        "set_recipe_nutrition",
    }

    def _get_tool_status_message(self, tool_name: str) -> str:
        """Get user-friendly status message for kitchen tool execution"""
        status_messages = {
            "set_ingredients": "gathering ingredients",
            "update_ingredients": "updating ingredients",
            "set_timer": "setting timer",
            "set_session_name": "preparing recipe",
            "set_recipe_metadata": "creating recipe",
            "set_recipe_ingredients": "adding ingredients",
            "set_recipe_steps": "writing steps",
            "set_recipe_nutrition": "calculating nutrition",
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

    def _accumulate_recipe_from_message(self, recipe: Dict, message: dict) -> Dict:
        """
        Accumulate recipe data from Redis message.
        Same logic as API service's handle_recipe_update_message().

        Args:
            recipe: Current recipe object to update
            message: Redis message dictionary

        Returns:
            Updated recipe object
        """
        content = message.get("content", {})
        if content.get("type") != "recipe_update":
            return recipe

        action = content.get("action")

        if action == "set_metadata":
            if content.get("name"):
                recipe["name"] = content.get("name")
            if content.get("description"):
                recipe["description"] = content.get("description")
            if content.get("difficulty"):
                recipe["difficulty"] = content.get("difficulty")
            if content.get("total_time_minutes"):
                recipe["total_time_minutes"] = content.get("total_time_minutes")
            if content.get("servings"):
                recipe["servings"] = content.get("servings")
            if content.get("tags"):
                recipe["tags"] = content.get("tags")

        elif action == "set_ingredients":
            recipe["ingredients"] = content.get("ingredients", [])

        elif action == "set_steps":
            recipe["steps"] = content.get("steps", [])

        elif action == "set_nutrition":
            recipe["nutrition"] = content.get("nutrition", {})

        return recipe

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
        """Execute tool calls with step-aware deduplication and Redis subscription for recipe tools"""
        last_message = state["messages"][-1]
        tool_results = []

        # Get current state
        current_step = state.get("current_step") or {}
        tools_called = list(current_step.get("tools_called", []))
        recipe = dict(state.get("recipe") or {})

        if not hasattr(last_message, "tool_calls"):
            return {"messages": tool_results}

        # Check if any recipe creation tools are being called
        has_recipe_tools = any(
            tc.get("name") in self.RECIPE_TOOLS
            for tc in last_message.tool_calls
        )

        if has_recipe_tools:
            # Subscribe to Redis and execute tools concurrently
            recipe = await self._execute_with_redis_subscription(
                state, last_message.tool_calls, tool_results, tools_called, recipe
            )
        else:
            # Normal tool execution
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

        # Check if recipe is complete (has required fields)
        recipe_complete = all([
            recipe.get("name"),
            recipe.get("ingredients"),
            recipe.get("steps")
        ])

        # Update current_step with new tools_called
        updated_step = (
            {**current_step, "tools_called": tools_called} if current_step else None
        )

        return {
            "messages": tool_results,
            "current_step": updated_step,
            "recipe": recipe if recipe else None,
            "recipe_generation_mode": not recipe_complete,
        }

    async def _execute_with_redis_subscription(
        self,
        state: KitchenAgentState,
        tool_calls: List,
        tool_results: List,
        tools_called: List,
        recipe: Dict,
    ) -> Dict:
        """
        Execute tools while subscribed to Redis to capture recipe updates.

        Args:
            state: Current agent state
            tool_calls: List of tool calls to execute
            tool_results: List to append tool results to
            tools_called: List of tools called for deduplication
            recipe: Current recipe object to accumulate into

        Returns:
            Updated recipe object with accumulated data from Redis messages
        """
        session_id = state["session_id"]
        channel = f"session:{session_id}"
        current_step = state.get("current_step") or {}

        # Create a dedicated Redis connection for subscription
        await self.redis_client._ensure_connected()
        pubsub = self.redis_client._client.pubsub()
        await pubsub.subscribe(channel)

        try:
            # Collect Redis messages in this list
            collected_messages = []
            stop_collecting = asyncio.Event()

            async def collect_messages():
                """Background task to collect Redis messages"""
                try:
                    async for message in pubsub.listen():
                        if stop_collecting.is_set():
                            break
                        if message["type"] == "message":
                            try:
                                data = json.loads(message["data"])
                                if self.redis_client.is_agent_message(data, "recipe_update"):
                                    collected_messages.append(data)
                                    logger.debug(f"📥 Collected recipe_update message: {data.get('content', {}).get('action')}")
                            except json.JSONDecodeError:
                                pass
                except asyncio.CancelledError:
                    pass

            # Start message collector in background
            collector_task = asyncio.create_task(collect_messages())

            # Execute all tools
            for tool_call in tool_calls:
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

            # Give Redis a moment to deliver messages
            await asyncio.sleep(0.1)

            # Stop collector
            stop_collecting.set()
            collector_task.cancel()
            try:
                await collector_task
            except asyncio.CancelledError:
                pass

            # Accumulate recipe from collected messages
            for msg in collected_messages:
                recipe = self._accumulate_recipe_from_message(recipe, msg)

            logger.info(f"📦 Accumulated recipe from {len(collected_messages)} messages: {recipe.get('name', 'unnamed')}")

            # If recipe was accumulated, save to DB for persistence
            if recipe and recipe.get("name"):
                try:
                    # Import here to avoid circular dependency
                    import sys
                    sys.path.insert(0, '/app')
                    from app.services import database_service
                    await database_service.save_session_recipe(session_id, recipe)
                    logger.info(f"💾 Persisted accumulated recipe to DB")
                except Exception as e:
                    logger.error(f"❌ Failed to persist recipe: {e}")

        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

        return recipe

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

        # Recipe comes from session_data (loaded from DB if recipe_id exists)
        recipe_data = session_data.get("recipe")
        has_valid_recipe = recipe_data and recipe_data.get("steps")

        # Calculate current step only if we have a valid recipe
        current_step = None
        if has_valid_recipe:
            ingredients = session_data.get("ingredients", [])
            current_step = self._calculate_current_step(recipe_data, ingredients)
            if current_step:
                logger.debug(
                    f"📍 Current step: {current_step.get('index')} - {current_step.get('instruction')[:50]}..."
                )
        else:
            logger.info("🍳 No recipe found - entering recipe generation mode")

        # Create initial state with recipe tracking for kitchen mode
        initial_state: KitchenAgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "system_prompt": system_prompt,
            "has_generated_text": False,
            "current_step": current_step,
            "recipe": recipe_data,  # Same object, whether loaded or empty/None
            "recipe_generation_mode": not has_valid_recipe,
        }

        accumulated_content = []
        message_id = f"msg-{uuid.uuid4()}"

        # Stream through the graph
        async for msg, metadata in self.graph.astream(
            initial_state, stream_mode="messages"
        ):
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
            message_id=message_id,
        )
