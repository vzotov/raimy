"""
Unified Agent

Single agent that handles all intents: recipe creation, cooking guidance,
Q&A, saving, shopping lists, and image generation.
"""

import os
import uuid
import logging
import random
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .prompt import (
    ANALYZE_INTENT_PROMPT,
    ANSWER_QUESTION_PROMPT,
    COOKING_COMPLETE_PROMPT,
    GENERAL_RESPONSE_PROMPT,
    GENERATE_STEP_GUIDANCE_PROMPT,
    GREETING_PROMPT,
    GREETING_TIPS,
    GREETING_WITH_RECIPE_PROMPT,
    NO_RECIPE_PROMPT,
    SAVE_RECIPE_PROMPT,
    SHOPPING_LIST_PROMPT,
    TIMER_CONFIRMATION_PROMPT,
    TIMER_QUESTION_PROMPT,
)
from .schemas import UnifiedIntentSchema, UnifiedStepGuidanceSchema
from ..base import AgentEvent, BaseAgent
from ..recipe_creator.agent import RecipeCreatorAgent

_IMAGE_GEN_ENABLED = bool(os.getenv("IMAGE_GEN_ENABLED"))
if _IMAGE_GEN_ENABLED:
    from ..image_gen.agent import ImageGenAgent

logger = logging.getLogger(__name__)


@dataclass
class UnifiedEvent(AgentEvent):
    """
    Event emitted during unified agent processing.

    Event types:
    - "text": Conversational response
    - "thinking": Status messages
    - "session_name": Session name update
    - "metadata": Recipe metadata (from recipe creation)
    - "ingredients": Recipe ingredients (from recipe creation)
    - "steps": Recipe steps (from recipe creation)
    - "nutrition": Recipe nutrition (from recipe creation)
    - "recipe_created": Full recipe object for DB persistence
    - "kitchen_step": Step guidance with next_step_prompt and optional timer
    - "selector": Options for user to choose from
    - "save_complete": Recipe saved to library
    - "shopping_list": Ingredients for buying
    - "generate_images": Trigger background image generation
    - "cooking_complete": All steps done
    - "step_image": Step image from image gen pass-through
    - "agent_state": State to persist
    - "complete": End of response stream
    """

    type: Literal[
        "text",
        "thinking",
        "session_name",
        "metadata",
        "ingredients",
        "steps",
        "nutrition",
        "recipe_created",
        "kitchen_step",
        "selector",
        "save_complete",
        "shopping_list",
        "generate_images",
        "cooking_complete",
        "step_image",
        "agent_state",
        "complete",
    ]
    data: Any


class UnifiedAgent(BaseAgent):
    """Single agent handling all intents for the unified chat experience"""

    MODEL = "gpt-5.4-mini"

    def __init__(self):
        self.llm = ChatOpenAI(
            model=self.MODEL,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.recipe_creator = RecipeCreatorAgent()
        self.image_gen = ImageGenAgent() if _IMAGE_GEN_ENABLED else None
        logger.info(f"🤖 UnifiedAgent initialized with model: {self.MODEL}")

    async def generate_greeting(self, recipe_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a personalized greeting for new sessions."""
        if recipe_name:
            prompt = GREETING_WITH_RECIPE_PROMPT.format(recipe_name=recipe_name)
            response = await self.llm.ainvoke(prompt)
            logger.info(f"👋 Generated greeting with recipe: {recipe_name}")
            return {
                "greeting": response.content,
                "message_type": "kitchen-step",
                "next_step_prompt": "Start cooking",
            }
        else:
            tip = random.choice(GREETING_TIPS)
            prompt = GREETING_PROMPT.format(tip=tip)
            response = await self.llm.ainvoke(prompt)
            logger.info("👋 Generated greeting (no recipe)")
            return {
                "greeting": response.content,
                "message_type": "text",
            }

    def _format_message_history(self, messages: List[BaseMessage]) -> str:
        """Format message history for prompts"""
        if not messages:
            return "(No previous messages)"
        formatted = []
        for msg in messages[-6:]:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    def _format_ingredients_list(self, recipe: Dict[str, Any]) -> str:
        """Format ingredients list for prompts"""
        ingredients = recipe.get("ingredients", [])
        if not ingredients:
            return "(No ingredients)"
        lines = []
        for ing in ingredients:
            amount = ing.get("amount", "")
            unit = ing.get("unit", "")
            name = ing.get("name", "")
            amount_str = f"{amount} {unit}".strip()
            lines.append(f'- {name} ({amount_str})' if amount_str else f'- {name}')
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

    def _extract_text_content(self, content: Any) -> str:
        """Extract plain text from message content for history conversion"""
        if isinstance(content, dict):
            msg_type = content.get("type", "")
            if msg_type == "text":
                return content.get("content", "")
            elif msg_type == "selector":
                message = content.get("message", "")
                options = content.get("options", [])
                if options:
                    options_text = "\n".join([
                        f"• {opt.get('text', '')} – {opt.get('description', '')}"
                        for opt in options
                    ])
                    return f"{message}\n\n{options_text}"
                return message
            elif msg_type == "kitchen-step":
                return content.get("message", "")
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

    async def _analyze_intent(
        self,
        message: str,
        langchain_messages: List[BaseMessage],
        session_data: Dict[str, Any],
    ) -> UnifiedIntentSchema:
        """Analyze user message to determine intent"""
        recipe = session_data.get("recipe")
        agent_state = session_data.get("agent_state") or {}
        current_step = agent_state.get("current_step")

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

        message_history = self._format_message_history(langchain_messages[:-1])

        prompt = ANALYZE_INTENT_PROMPT.format(
            user_memory=session_data.get("user_memory") or "(No user profile available)",
            has_recipe=has_recipe,
            current_step_info=current_step_info,
            recipe_name=recipe_name,
            message_history=message_history,
            user_message=message,
        )

        llm_with_output = self.llm.with_structured_output(UnifiedIntentSchema)
        result: UnifiedIntentSchema = await llm_with_output.ainvoke(prompt)
        logger.info(f"📊 Unified intent: {result.intent}")
        return result

    async def _handle_recipe_creation(
        self,
        request: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Delegate to RecipeCreatorAgent and emit proactive selector on completion"""
        session_data_for_recipe = {**session_data, "recipe": None}
        accumulated_recipe: Dict[str, Any] = {}

        async for event in self.recipe_creator.run_streaming(
            message=request,
            message_history=message_history,
            session_id=session_id,
            session_data=session_data_for_recipe,
        ):
            if event.type == "metadata":
                accumulated_recipe.update(event.data)
                yield UnifiedEvent(type="metadata", data=event.data)
            elif event.type == "ingredients":
                accumulated_recipe["ingredients"] = event.data
                yield UnifiedEvent(type="ingredients", data=event.data)
            elif event.type == "steps":
                accumulated_recipe["steps"] = event.data
                yield UnifiedEvent(type="steps", data=event.data)
            elif event.type == "nutrition":
                accumulated_recipe["nutrition"] = event.data
                yield UnifiedEvent(type="nutrition", data=event.data)
            elif event.type == "session_name":
                accumulated_recipe["name"] = event.data
                yield UnifiedEvent(type="session_name", data=event.data)
            elif event.type == "complete":
                pass  # We emit complete ourselves
            else:
                yield UnifiedEvent(type=event.type, data=event.data)

        has_valid_recipe = all([
            accumulated_recipe.get("name"),
            accumulated_recipe.get("ingredients"),
            accumulated_recipe.get("steps"),
        ])

        if has_valid_recipe:
            yield UnifiedEvent(type="recipe_created", data=accumulated_recipe)
            logger.info(f"📝 Recipe created: {accumulated_recipe.get('name')}")

            message_id = f"offer-{session_id}-{uuid.uuid4().hex[:8]}"
            yield UnifiedEvent(type="selector", data={
                "message": "Your recipe is ready! What would you like to do next?",
                "options": [
                    {"text": "Start Cooking", "description": "Get step-by-step guidance"},
                    {"text": "Save Recipe", "description": "Save to your recipe library"},
                    {"text": "Buy Ingredients", "description": "Get a shopping list"},
                ],
                "message_id": message_id,
            })

    async def _handle_step_action(
        self,
        intent: str,
        message: str,
        langchain_messages: List[BaseMessage],
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle start_cooking, next_step, previous_step"""
        recipe = session_data.get("recipe")
        agent_state = session_data.get("agent_state") or {}
        current_step = agent_state.get("current_step")
        message_id = f"msg-{uuid.uuid4()}"

        if not recipe or not recipe.get("steps"):
            message_history = self._format_message_history(langchain_messages[:-1])
            prompt = NO_RECIPE_PROMPT.format(
                message_history=message_history,
                user_message=message,
            )
            response = await self.llm.ainvoke(prompt)
            yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
            return

        steps = recipe.get("steps", [])
        total_steps = len(steps)

        # Calculate new step index
        if intent == "start_cooking":
            new_step = 0
        elif intent == "next_step":
            if current_step is None:
                new_step = 0
            elif current_step >= total_steps - 1:
                # Already at/past last step — trigger completion
                prompt = COOKING_COMPLETE_PROMPT.format(recipe_name=recipe.get("name", "your dish"))
                response = await self.llm.ainvoke(prompt)
                yield UnifiedEvent(type="cooking_complete", data=None)
                yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
                yield UnifiedEvent(type="agent_state", data={"current_step": current_step})
                return
            else:
                new_step = current_step + 1
        elif intent == "previous_step":
            new_step = max(0, (current_step or 0) - 1)
        else:
            new_step = current_step if current_step is not None else 0

        # Last step triggers completion (it's the "enjoy your meal" step)
        if new_step == total_steps - 1:
            prompt = COOKING_COMPLETE_PROMPT.format(recipe_name=recipe.get("name", "your dish"))
            response = await self.llm.ainvoke(prompt)
            yield UnifiedEvent(type="cooking_complete", data=None)
            yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
            yield UnifiedEvent(type="agent_state", data={"current_step": new_step})
            return

        # Generate step guidance
        step_data = steps[new_step]
        step_instruction = step_data.get("instruction", "")
        step_duration = step_data.get("duration_minutes") or step_data.get("duration")
        step_image_url = step_data.get("image_url")

        message_history = self._format_message_history(langchain_messages[:-1])

        prompt = GENERATE_STEP_GUIDANCE_PROMPT.format(
            user_memory=session_data.get("user_memory") or "(No user profile available)",
            recipe_name=recipe.get("name", "Recipe"),
            step_number=new_step + 1,
            total_steps=total_steps,
            step_instruction=step_instruction,
            step_duration=f"{step_duration} minutes" if step_duration else "No specific duration",
            ingredients_list=self._format_ingredients_list(recipe),
            all_steps=self._format_all_steps(recipe),
            message_history=message_history,
            user_message=message,
        )

        llm_with_output = self.llm.with_structured_output(UnifiedStepGuidanceSchema)
        guidance: UnifiedStepGuidanceSchema = await llm_with_output.ainvoke(prompt)

        logger.info(f"📋 Step {new_step + 1}/{total_steps} guidance generated")

        yield UnifiedEvent(type="kitchen_step", data={
            "message": guidance.spoken_response,
            "message_id": message_id,
            "next_step_prompt": guidance.next_step_prompt,
            "image_url": step_image_url,
            "timer_minutes": guidance.suggested_timer_minutes,
            "timer_label": guidance.timer_label,
        })
        yield UnifiedEvent(type="agent_state", data={"current_step": new_step})

    async def _handle_timer(
        self,
        intent_result: UnifiedIntentSchema,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle explicit timer request"""
        timer_minutes = intent_result.timer_minutes
        timer_label = intent_result.timer_label or "Timer"
        message_id = f"msg-{uuid.uuid4()}"

        if not timer_minutes:
            prompt = TIMER_QUESTION_PROMPT.format(user_message="set a timer")
            response = await self.llm.ainvoke(prompt)
            yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
            return

        prompt = TIMER_CONFIRMATION_PROMPT.format(
            timer_minutes=timer_minutes,
            timer_label=timer_label,
        )
        response = await self.llm.ainvoke(prompt)
        yield UnifiedEvent(type="kitchen_step", data={
            "message": response.content,
            "message_id": message_id,
            "next_step_prompt": "Timer done",
            "timer_minutes": timer_minutes,
            "timer_label": timer_label,
        })

    async def _handle_save_recipe(
        self,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle save_recipe intent"""
        recipe = session_data.get("recipe")
        message_id = f"msg-{uuid.uuid4()}"

        if not recipe:
            yield UnifiedEvent(type="text", data={
                "content": "No recipe to save yet. Create a recipe first!",
                "message_id": message_id,
            })
            return

        prompt = SAVE_RECIPE_PROMPT.format(recipe_name=recipe.get("name", "your recipe"))
        response = await self.llm.ainvoke(prompt)
        yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
        yield UnifiedEvent(type="save_complete", data={"recipe": recipe})

    async def _handle_shopping_list(
        self,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle buy_ingredients intent"""
        recipe = session_data.get("recipe")
        message_id = f"msg-{uuid.uuid4()}"

        if not recipe or not recipe.get("ingredients"):
            yield UnifiedEvent(type="text", data={
                "content": "No recipe loaded yet. Create a recipe first!",
                "message_id": message_id,
            })
            return

        ingredients = recipe.get("ingredients", [])
        shopping_items = [
            {
                "name": ing.get("name", ""),
                "eng_name": ing.get("eng_name") or "",
                "amount": ing.get("amount", ""),
                "unit": ing.get("unit", ""),
            }
            for ing in ingredients
        ]

        prompt = SHOPPING_LIST_PROMPT.format(recipe_name=recipe.get("name", "your recipe"))
        response = await self.llm.ainvoke(prompt)
        yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
        yield UnifiedEvent(type="shopping_list", data={
            "items": shopping_items,
            "recipe_name": recipe.get("name"),
        })

    async def _handle_image_gen(
        self,
        message: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle generate_images intent"""
        message_id = f"msg-{uuid.uuid4()}"

        if not os.getenv("IMAGE_GEN_ENABLED"):
            yield UnifiedEvent(type="text", data={
                "content": "Image generation is not available.",
                "message_id": message_id,
            })
            return

        existing_recipe = session_data.get("recipe") or {}
        if not existing_recipe.get("steps"):
            yield UnifiedEvent(type="text", data={
                "content": "No recipe found. Create a recipe first to generate step images.",
                "message_id": message_id,
            })
            return

        missing = [i for i, s in enumerate(existing_recipe["steps"]) if not s.get("image_url")]
        if not missing:
            yield UnifiedEvent(type="text", data={
                "content": "All steps already have images.",
                "message_id": message_id,
            })
            return

        yield UnifiedEvent(type="text", data={
            "content": f"Generating images for {len(missing)} steps...",
            "message_id": message_id,
        })
        yield UnifiedEvent(type="generate_images", data={"message_id": message_id})

    async def _handle_question(
        self,
        question: str,
        langchain_messages: List[BaseMessage],
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle answer_question intent"""
        recipe = session_data.get("recipe")
        agent_state = session_data.get("agent_state") or {}
        current_step = agent_state.get("current_step")
        message_id = f"msg-{uuid.uuid4()}"

        if not recipe:
            message_history = self._format_message_history(langchain_messages[:-1])
            prompt = NO_RECIPE_PROMPT.format(
                message_history=message_history,
                user_message=question,
            )
            response = await self.llm.ainvoke(prompt)
            yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})
            return

        steps = recipe.get("steps", [])
        total_steps = len(steps)

        if current_step is not None and 0 <= current_step < total_steps:
            step_instruction = steps[current_step].get("instruction", "")
            step_number = current_step + 1
        else:
            step_instruction = "Not started yet"
            step_number = 0

        message_history = self._format_message_history(langchain_messages[:-1])

        prompt = ANSWER_QUESTION_PROMPT.format(
            user_memory=session_data.get("user_memory") or "(No user profile available)",
            recipe_name=recipe.get("name", "Recipe"),
            step_number=step_number,
            total_steps=total_steps,
            step_instruction=step_instruction,
            all_steps=self._format_all_steps(recipe),
            ingredients_list=self._format_ingredients_list(recipe),
            message_history=message_history,
            question=question,
        )

        response = await self.llm.ainvoke(prompt)
        yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})

    async def _handle_general_chat(
        self,
        message: str,
        langchain_messages: List[BaseMessage],
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """Handle general_chat intent"""
        recipe = session_data.get("recipe")
        agent_state = session_data.get("agent_state") or {}
        current_step = agent_state.get("current_step")
        message_id = f"msg-{uuid.uuid4()}"

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

        message_history = self._format_message_history(langchain_messages[:-1])

        prompt = GENERAL_RESPONSE_PROMPT.format(
            has_recipe=has_recipe,
            recipe_name=recipe_name,
            current_step_info=current_step_info,
            message_history=message_history,
            user_message=message,
        )

        response = await self.llm.ainvoke(prompt)
        yield UnifiedEvent(type="text", data={"content": response.content, "message_id": message_id})

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[UnifiedEvent, None]:
        """
        Process a user message and yield events.

        Routes to the appropriate handler based on intent analysis.
        """
        langchain_messages = self._convert_message_history(message_history)
        langchain_messages.append(HumanMessage(content=message))

        logger.info(f"💬 Unified agent processing session={session_id}")

        yield UnifiedEvent(type="thinking", data="thinking")

        intent_result = await self._analyze_intent(message, langchain_messages, session_data)
        intent = intent_result.intent

        if intent in ("create_recipe", "modify_recipe"):
            request = (
                intent_result.recipe_request
                or intent_result.modification_request
                or message
            )
            async for event in self._handle_recipe_creation(request, message_history, session_id, session_data):
                yield event

        elif intent in ("start_cooking", "next_step", "previous_step"):
            async for event in self._handle_step_action(intent, message, langchain_messages, session_data):
                yield event

        elif intent == "set_timer":
            async for event in self._handle_timer(intent_result, session_data):
                yield event

        elif intent == "save_recipe":
            async for event in self._handle_save_recipe(session_data):
                yield event

        elif intent == "buy_ingredients":
            async for event in self._handle_shopping_list(session_data):
                yield event

        elif intent == "generate_images":
            async for event in self._handle_image_gen(message, message_history, session_id, session_data):
                yield event

        elif intent == "answer_question":
            async for event in self._handle_question(
                intent_result.question or message, langchain_messages, session_data
            ):
                yield event

        else:  # general_chat
            async for event in self._handle_general_chat(message, langchain_messages, session_data):
                yield event

        yield UnifiedEvent(type="complete", data=None)
