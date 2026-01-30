"""
Kitchen Agent for Active Cooking Guidance

Uses generator streaming (like recipe creator) with:
- Intent analysis for routing user messages
- Recipe creation (delegates to RecipeCreatorAgent)
- Step-by-step cooking guidance with hybrid tracking
- Current step persistence via agent_state column
"""

import os
import uuid
import logging
from dataclasses import dataclass
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    Annotated,
)

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

import random

from .prompt import (
    KITCHEN_SYSTEM_PROMPT,
    ANALYZE_INTENT_PROMPT,
    GENERATE_STEP_GUIDANCE_PROMPT,
    ANSWER_QUESTION_PROMPT,
    HANDLE_RECIPE_REQUEST_PROMPT,
    GENERAL_RESPONSE_PROMPT,
    NO_RECIPE_PROMPT,
    COOKING_COMPLETE_PROMPT,
    TIMER_QUESTION_PROMPT,
    TIMER_CONFIRMATION_PROMPT,
    RECIPE_READY_PROMPT,
    GREETING_PROMPT,
    GREETING_WITH_RECIPE_PROMPT,
    GREETING_TIPS,
)
from .schemas import (
    KitchenIntentAnalysis,
    StepGuidanceResponse,
    QuestionResponse,
)
from ..base import AgentEvent, BaseAgent
from ..recipe_creator.agent import RecipeCreatorAgent

logger = logging.getLogger(__name__)


@dataclass
class KitchenEvent(AgentEvent):
    """
    Event emitted during kitchen agent processing.

    Event types:
    - "text": Conversational response (no buttons)
    - "kitchen_step": Step guidance with next_step_prompt (shows buttons)
    - "thinking": Status messages
    - "ingredients_highlight": Ingredient state changes (update)
    - "ingredients_set": Initial ingredient setup
    - "timer": Set cooking timer
    - "session_name": Session name update
    - "recipe_created": Full recipe object for DB persistence
    - "agent_state": State to persist
    - "complete": End of response
    """

    type: Literal[
        "text",
        "kitchen_step",
        "thinking",
        "ingredients_highlight",
        "ingredients_set",
        "timer",
        "session_name",
        "recipe_created",
        "agent_state",
        "complete",
    ]
    data: Any


class KitchenAgentState(TypedDict):
    """State for the kitchen agent graph"""

    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    user_message: str

    # Recipe data (from session)
    recipe: Optional[Dict[str, Any]]
    current_step: Optional[int]  # None = not started, 0+ = step index
    ingredients: Optional[List[Dict]]

    # Analysis results
    intent: Optional[Literal[
        "get_recipe", "start_cooking", "next_step",
        "previous_step", "ask_question", "set_timer", "general_chat"
    ]]
    recipe_request: Optional[str]
    question: Optional[str]
    timer_minutes: Optional[int]
    timer_label: Optional[str]

    # Response data
    text_response: Optional[str]
    next_step_prompt: Optional[str]
    ingredients_to_update: Optional[List[Dict]]
    timer_to_set: Optional[Dict]
    new_step_index: Optional[int]


# Thinking messages for nodes
THINKING_MESSAGES = {
    "get_recipe": "creating recipe",
    "step_action": "preparing guidance",
    "question": "thinking",
    "timer": "setting timer",
}


class KitchenAgent(BaseAgent):
    """Agent for active kitchen cooking guidance with generator streaming"""

    MODEL = "gpt-4o-mini"

    def __init__(self):
        """Initialize the kitchen agent"""
        self.llm = ChatOpenAI(
            model=self.MODEL,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.recipe_creator = RecipeCreatorAgent()
        logger.info(f"🍳 KitchenAgent initialized with model: {self.MODEL}")
        self.graph = self._build_graph()

    async def generate_greeting(self, recipe_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate a personalized greeting for new sessions.

        Args:
            recipe_name: Optional recipe name if session has a pre-loaded recipe

        Returns:
            Dict with greeting, message_type, and optional next_step_prompt
        """
        if recipe_name:
            # Recipe loaded - use recipe-specific prompt and return kitchen-step
            prompt = GREETING_WITH_RECIPE_PROMPT.format(recipe_name=recipe_name)
            response = await self.llm.ainvoke(prompt)
            logger.info(f"👋 Generated kitchen greeting with recipe: {recipe_name}")
            return {
                "greeting": response.content,
                "message_type": "kitchen-step",
                "next_step_prompt": "Start cooking",
            }
        else:
            # No recipe - use tip-based prompt and return text
            tip = random.choice(GREETING_TIPS)
            prompt = GREETING_PROMPT.format(
                session_type="kitchen",
                tip=tip,
            )
            response = await self.llm.ainvoke(prompt)
            logger.info(f"👋 Generated kitchen greeting (tip: {tip[:30]}...)")
            return {
                "greeting": response.content,
                "message_type": "text",
            }

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for kitchen guidance"""
        workflow = StateGraph(KitchenAgentState)

        # Add nodes
        workflow.add_node("analyze", self._analyze_intent)
        workflow.add_node("get_recipe", self._get_recipe)
        workflow.add_node("step_action", self._step_action)
        workflow.add_node("question", self._answer_question)
        workflow.add_node("timer", self._set_timer)
        workflow.add_node("respond", self._generate_response)

        # Entry point
        workflow.set_entry_point("analyze")

        # Route from analyze based on intent
        workflow.add_conditional_edges(
            "analyze",
            self._route_intent,
            {
                "get_recipe": "get_recipe",
                "step_action": "step_action",
                "question": "question",
                "timer": "timer",
                "respond": "respond",
            },
        )

        # All nodes except get_recipe end after respond
        workflow.add_edge("step_action", "respond")
        workflow.add_edge("question", "respond")
        workflow.add_edge("timer", "respond")
        workflow.add_edge("respond", END)

        # get_recipe ends directly (handles its own events via RecipeCreatorAgent)
        workflow.add_edge("get_recipe", END)

        return workflow.compile()

    def _format_message_history(self, messages: List[BaseMessage]) -> str:
        """Format message history for prompts"""
        if not messages:
            return "(No previous messages)"

        formatted = []
        for msg in messages[-6:]:  # Last 6 messages for context
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    def _format_ingredients_list(self, recipe: Dict[str, Any]) -> str:
        """Format ingredients list for prompts with name clearly separated"""
        ingredients = recipe.get("ingredients", [])
        if not ingredients:
            return "(No ingredients)"

        lines = []
        for ing in ingredients:
            amount = ing.get("amount", "")
            unit = ing.get("unit", "")
            name = ing.get("name", "")
            # Format: NAME: "ingredient name" (amount unit)
            # This makes it clear the name is just the quoted part
            amount_str = f"{amount} {unit}".strip()
            if amount_str:
                line = f'- NAME: "{name}" ({amount_str})'
            else:
                line = f'- NAME: "{name}"'
            lines.append(line)
        return "\n".join(lines)

    def _format_all_steps(self, recipe: Dict[str, Any]) -> str:
        """Format all steps for prompts"""
        steps = recipe.get("steps", [])
        if not steps:
            return "(No steps)"

        lines = []
        for i, step in enumerate(steps, 1):
            instruction = step.get("instruction", "")
            duration = step.get("duration_minutes") or step.get("duration")
            line = f"{i}. {instruction}"
            if duration:
                line += f" [{duration} min]"
            lines.append(line)
        return "\n".join(lines)

    async def _analyze_intent(self, state: KitchenAgentState) -> Dict:
        """Analyze user message to determine intent"""
        recipe = state.get("recipe")
        current_step = state.get("current_step")

        # Prepare context
        has_recipe = recipe is not None and recipe.get("steps")
        recipe_name = recipe.get("name", "None") if recipe else "None"

        if current_step is not None and recipe:
            steps = recipe.get("steps", [])
            if 0 <= current_step < len(steps):
                current_step_info = f"Step {current_step + 1} of {len(steps)}"
            else:
                current_step_info = "Completed all steps"
        else:
            current_step_info = "Not started"

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = ANALYZE_INTENT_PROMPT.format(
            has_recipe=has_recipe,
            current_step_info=current_step_info,
            recipe_name=recipe_name,
            message_history=message_history,
            user_message=state["user_message"],
        )

        llm_with_output = self.llm.with_structured_output(KitchenIntentAnalysis)
        result: KitchenIntentAnalysis = await llm_with_output.ainvoke(prompt)

        logger.info(f"📊 Kitchen intent: {result.intent}")

        return {
            "intent": result.intent,
            "recipe_request": result.recipe_request,
            "question": result.question,
            "timer_minutes": result.timer_minutes,
            "timer_label": result.timer_label,
        }

    def _route_intent(self, state: KitchenAgentState) -> str:
        """Route based on analyzed intent"""
        intent = state.get("intent")

        if intent == "get_recipe":
            return "get_recipe"
        if intent in ("start_cooking", "next_step", "previous_step"):
            return "step_action"
        if intent == "ask_question":
            return "question"
        if intent == "set_timer":
            return "timer"
        return "respond"

    async def _get_recipe(self, state: KitchenAgentState) -> Dict:
        """
        Handle recipe acquisition by delegating to RecipeCreatorAgent.
        Sets text_response to indicate recipe creation was triggered.
        """
        # The actual recipe generation happens in run_streaming where we
        # iterate over RecipeCreatorAgent.run_streaming() and yield events
        recipe_request = state.get("recipe_request") or state["user_message"]

        return {
            "recipe_request": recipe_request,
            "text_response": "__RECIPE_CREATION__",  # Special marker
        }

    async def _step_action(self, state: KitchenAgentState) -> Dict:
        """Handle step navigation (start, next, previous)"""
        intent = state.get("intent")
        recipe = state.get("recipe")
        current_step = state.get("current_step")

        if not recipe or not recipe.get("steps"):
            # Generate no-recipe response using LLM
            prompt = NO_RECIPE_PROMPT.format(user_message=state["user_message"])
            response = await self.llm.ainvoke(prompt)
            return {"text_response": response.content}

        steps = recipe.get("steps", [])
        total_steps = len(steps)

        # Calculate new step index
        if intent == "start_cooking":
            new_step = 0
        elif intent == "next_step":
            if current_step is None:
                new_step = 0
            elif current_step >= total_steps - 1:
                # Completed all steps - mark all ingredients as used
                all_used = [
                    {"name": ing.get("name"), "highlighted": False, "used": True}
                    for ing in recipe.get("ingredients", [])
                ]
                # Generate completion message using LLM
                prompt = COOKING_COMPLETE_PROMPT.format(
                    recipe_name=recipe.get("name", "your dish"),
                )
                response = await self.llm.ainvoke(prompt)
                return {
                    "text_response": response.content,
                    "new_step_index": current_step,
                    "ingredients_to_update": all_used,
                }
            else:
                new_step = current_step + 1
        elif intent == "previous_step":
            if current_step is None or current_step <= 0:
                new_step = 0
            else:
                new_step = current_step - 1
        else:
            new_step = current_step if current_step is not None else 0

        # Get step data
        step_data = steps[new_step]
        step_instruction = step_data.get("instruction", "")
        step_duration = step_data.get("duration_minutes") or step_data.get("duration")

        # Generate step guidance using LLM
        message_history = self._format_message_history(state["messages"][:-1])

        prompt = GENERATE_STEP_GUIDANCE_PROMPT.format(
            recipe_name=recipe.get("name", "Recipe"),
            step_number=new_step + 1,
            total_steps=total_steps,
            step_instruction=step_instruction,
            step_duration=f"{step_duration} minutes" if step_duration else "No specific duration",
            ingredients_list=self._format_ingredients_list(recipe),
            all_steps=self._format_all_steps(recipe),
            message_history=message_history,
            user_message=state["user_message"],
        )

        llm_with_output = self.llm.with_structured_output(StepGuidanceResponse)
        guidance: StepGuidanceResponse = await llm_with_output.ainvoke(prompt)

        logger.info(f"📋 Step {new_step + 1} guidance: highlight={guidance.ingredients_to_highlight}, used={guidance.ingredients_to_mark_used}")

        # Build ingredient updates
        # Highlighted ingredients take precedence - filter them out from mark_as_used
        highlighted_set = set(guidance.ingredients_to_highlight)
        ingredients_to_update = []

        for ing_name in guidance.ingredients_to_mark_used:
            # Skip if this ingredient is also being highlighted (LLM mistake)
            if ing_name in highlighted_set:
                logger.warning(f"⚠️ Ingredient '{ing_name}' in both lists, keeping highlight only")
                continue
            ingredients_to_update.append({
                "name": ing_name,
                "highlighted": False,
                "used": True,
            })

        for ing_name in guidance.ingredients_to_highlight:
            ingredients_to_update.append({
                "name": ing_name,
                "highlighted": True,
            })

        # Build timer if suggested
        timer_to_set = None
        if guidance.suggested_timer_minutes:
            timer_to_set = {
                "duration": guidance.suggested_timer_minutes * 60,  # Convert to seconds
                "label": guidance.timer_label or f"Step {new_step + 1}",
            }

        return {
            "text_response": guidance.spoken_response,
            "next_step_prompt": guidance.next_step_prompt,
            "ingredients_to_update": ingredients_to_update if ingredients_to_update else None,
            "timer_to_set": timer_to_set,
            "new_step_index": new_step,
        }

    async def _answer_question(self, state: KitchenAgentState) -> Dict:
        """Answer a question about the current step or recipe"""
        recipe = state.get("recipe")
        current_step = state.get("current_step")
        question = state.get("question") or state["user_message"]

        if not recipe:
            # Generate no-recipe response using LLM
            prompt = NO_RECIPE_PROMPT.format(user_message=state["user_message"])
            response = await self.llm.ainvoke(prompt)
            return {"text_response": response.content}

        steps = recipe.get("steps", [])
        total_steps = len(steps)

        # Get current step info
        if current_step is not None and 0 <= current_step < total_steps:
            step_instruction = steps[current_step].get("instruction", "")
            step_number = current_step + 1
        else:
            step_instruction = "Not started yet"
            step_number = 0

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = ANSWER_QUESTION_PROMPT.format(
            recipe_name=recipe.get("name", "Recipe"),
            step_number=step_number,
            total_steps=total_steps,
            step_instruction=step_instruction,
            all_steps=self._format_all_steps(recipe),
            ingredients_list=self._format_ingredients_list(recipe),
            message_history=message_history,
            question=question,
        )

        llm_with_output = self.llm.with_structured_output(QuestionResponse)
        response: QuestionResponse = await llm_with_output.ainvoke(prompt)

        return {
            "text_response": response.answer,
        }

    async def _set_timer(self, state: KitchenAgentState) -> Dict:
        """Handle explicit timer request"""
        timer_minutes = state.get("timer_minutes")
        timer_label = state.get("timer_label")

        if not timer_minutes:
            # Generate timer question using LLM
            prompt = TIMER_QUESTION_PROMPT.format(user_message=state["user_message"])
            response = await self.llm.ainvoke(prompt)
            return {"text_response": response.content}

        timer_to_set = {
            "duration": timer_minutes * 60,  # Convert to seconds
            "label": timer_label or "Timer",
        }

        # Generate timer confirmation using LLM
        prompt = TIMER_CONFIRMATION_PROMPT.format(
            timer_minutes=timer_minutes,
            timer_label=timer_label or "Timer",
        )
        response = await self.llm.ainvoke(prompt)

        return {
            "text_response": response.content,
            "timer_to_set": timer_to_set,
        }

    async def _generate_response(self, state: KitchenAgentState) -> Dict:
        """Generate a general response for chat or other intents"""
        # If we already have a text response, don't generate another
        if state.get("text_response"):
            return {}

        recipe = state.get("recipe")
        current_step = state.get("current_step")

        has_recipe = recipe is not None and recipe.get("steps")
        recipe_name = recipe.get("name", "None") if recipe else "None"

        if current_step is not None and recipe:
            steps = recipe.get("steps", [])
            if 0 <= current_step < len(steps):
                current_step_info = f"Step {current_step + 1} of {len(steps)}"
            else:
                current_step_info = "Completed"
        else:
            current_step_info = "Not started"

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = GENERAL_RESPONSE_PROMPT.format(
            has_recipe=has_recipe,
            recipe_name=recipe_name,
            current_step_info=current_step_info,
            message_history=message_history,
            user_message=state["user_message"],
        )

        response = await self.llm.ainvoke(prompt)

        return {
            "text_response": response.content,
        }

    def _extract_text_content(self, content: Any) -> str:
        """Extract plain text from message content"""
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
    ) -> AsyncGenerator[KitchenEvent, None]:
        """
        Run the agent and yield events for kitchen guidance.

        Args:
            message: User message to process
            message_history: Previous message history from database
            session_id: Session ID for context
            session_data: Full session data including recipe and agent_state

        Yields:
            KitchenEvent for each action
        """
        # Convert message history and add new message
        langchain_messages = self._convert_message_history(message_history)
        langchain_messages.append(HumanMessage(content=message))

        logger.info(f"📚 Message history: {len(message_history)} messages")

        # Load existing state
        recipe_data = session_data.get("recipe")
        agent_state = session_data.get("agent_state") or {}
        current_step = agent_state.get("current_step")
        ingredients = session_data.get("ingredients", [])

        logger.info(f"📝 Session state: recipe={recipe_data.get('name') if recipe_data else None}, step={current_step}")

        # Create initial state
        initial_state: KitchenAgentState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "user_message": message,
            "recipe": recipe_data,
            "current_step": current_step,
            "ingredients": ingredients,
            "intent": None,
            "recipe_request": None,
            "question": None,
            "timer_minutes": None,
            "timer_label": None,
            "text_response": None,
            "next_step_prompt": None,
            "ingredients_to_update": None,
            "timer_to_set": None,
            "new_step_index": None,
        }

        message_id = f"msg-{uuid.uuid4()}"
        final_step_index = current_step

        # Stream through the graph
        async for event in self.graph.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in event.items():
                if not state_update:
                    continue

                logger.debug(f"📦 Node '{node_name}' update: {list(state_update.keys())}")

                # Send thinking message for generation nodes
                if node_name in THINKING_MESSAGES:
                    yield KitchenEvent(type="thinking", data=THINKING_MESSAGES[node_name])

                # Check for recipe creation marker
                text_response = state_update.get("text_response")
                if text_response == "__RECIPE_CREATION__":
                    # Delegate to RecipeCreatorAgent
                    recipe_request = state_update.get("recipe_request") or message

                    yield KitchenEvent(type="thinking", data="Creating recipe")

                    # Accumulate recipe data from RecipeCreatorAgent
                    accumulated_recipe = {}

                    # Stream events from RecipeCreatorAgent
                    async for recipe_event in self.recipe_creator.run_streaming(
                        message=recipe_request,
                        message_history=message_history,
                        session_id=session_id,
                        session_data=session_data,
                    ):
                        # Accumulate recipe document parts
                        if recipe_event.type == "metadata":
                            accumulated_recipe.update(recipe_event.data)
                        elif recipe_event.type == "ingredients":
                            accumulated_recipe["ingredients"] = recipe_event.data
                        elif recipe_event.type == "steps":
                            accumulated_recipe["steps"] = recipe_event.data
                        elif recipe_event.type == "nutrition":
                            accumulated_recipe["nutrition"] = recipe_event.data
                        elif recipe_event.type == "complete":
                            # Ignore complete from recipe creator - we handle completion ourselves
                            pass
                        elif recipe_event.type == "session_name":
                            # Pass through and also track the name
                            yield KitchenEvent(type="session_name", data=recipe_event.data)
                            accumulated_recipe["name"] = recipe_event.data
                        else:
                            # Pass through any other events (thinking, text, future types)
                            yield KitchenEvent(type=recipe_event.type, data=recipe_event.data)

                    # Check if we have a valid recipe (must have name, ingredients, and steps)
                    has_valid_recipe = all([
                        accumulated_recipe.get("name"),
                        accumulated_recipe.get("ingredients"),
                        accumulated_recipe.get("steps"),
                    ])

                    if has_valid_recipe:
                        # Emit recipe_created with full recipe object for DB persistence
                        yield KitchenEvent(type="recipe_created", data=accumulated_recipe)
                        logger.info(f"📝 Recipe created: {accumulated_recipe.get('name')}")

                        # Set up cooking ingredients for tracking
                        cooking_ingredients = [
                            {
                                "name": ing.get("name"),
                                "amount": ing.get("amount", ""),
                                "unit": ing.get("unit", ""),
                                "highlighted": False,
                                "used": False,
                            }
                            for ing in accumulated_recipe["ingredients"]
                        ]
                        yield KitchenEvent(type="ingredients_set", data=cooking_ingredients)
                        logger.info(f"🥗 Set up {len(cooking_ingredients)} cooking ingredients")

                        # Generate "ready to start" message using LLM - this is a kitchen_step
                        recipe_name = accumulated_recipe.get("name")
                        prompt = RECIPE_READY_PROMPT.format(recipe_name=recipe_name)
                        ready_response = await self.llm.ainvoke(prompt)
                        yield KitchenEvent(
                            type="kitchen_step",
                            data={
                                "message": ready_response.content,
                                "message_id": message_id,
                                "next_step_prompt": "Start cooking",
                            },
                        )
                    else:
                        # Recipe creation didn't produce a full recipe (e.g., user was just asking questions)
                        logger.warning(f"⚠️  Recipe creation incomplete: name={accumulated_recipe.get('name')}, "
                                     f"ingredients={bool(accumulated_recipe.get('ingredients'))}, "
                                     f"steps={bool(accumulated_recipe.get('steps'))}")
                        # Don't emit any events - let the conversation continue naturally

                    # Don't continue to other state handling
                    continue

                # Emit ingredient updates
                if state_update.get("ingredients_to_update"):
                    yield KitchenEvent(
                        type="ingredients_highlight",
                        data=state_update["ingredients_to_update"],
                    )

                # Emit timer
                if state_update.get("timer_to_set"):
                    timer_data = state_update["timer_to_set"]
                    yield KitchenEvent(
                        type="timer",
                        data=timer_data,
                    )

                # Track new step index for persistence
                if state_update.get("new_step_index") is not None:
                    final_step_index = state_update["new_step_index"]

                # Emit text or kitchen_step response
                if text_response and text_response != "__RECIPE_CREATION__":
                    next_step_prompt = state_update.get("next_step_prompt")
                    if next_step_prompt:
                        # Step guidance - emit kitchen_step with prompt
                        yield KitchenEvent(
                            type="kitchen_step",
                            data={
                                "message": text_response,
                                "message_id": message_id,
                                "next_step_prompt": next_step_prompt,
                            },
                        )
                    else:
                        # Regular text response (questions, timers, etc.)
                        yield KitchenEvent(
                            type="text",
                            data={
                                "content": text_response,
                                "message_id": message_id,
                            },
                        )

        # Emit agent state for persistence if step changed
        if final_step_index != current_step:
            new_agent_state = {
                "current_step": final_step_index,
                "completed_steps": agent_state.get("completed_steps", []),
            }
            # Add completed step if we moved forward
            if current_step is not None and final_step_index is not None:
                if final_step_index > current_step:
                    completed = list(new_agent_state.get("completed_steps", []))
                    if current_step not in completed:
                        completed.append(current_step)
                    new_agent_state["completed_steps"] = completed

            yield KitchenEvent(
                type="agent_state",
                data=new_agent_state,
            )

        yield KitchenEvent(type="complete", data=None)
