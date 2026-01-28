"""
Recipe Creator Agent with Structured Output Generation

Uses LangGraph for orchestrating recipe generation with:
- Fast model (GPT-4o-mini) for quick responses
- Sequential generation with state-based completeness checks
- Structured outputs for each recipe component
- Streaming events for real-time UI updates
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

from .prompt import (
    ANALYZE_REQUEST_PROMPT,
    ASK_QUESTION_PROMPT,
    FINAL_RESPONSE_PROMPT,
    GENERATE_INGREDIENTS_PROMPT,
    GENERATE_METADATA_PROMPT,
    GENERATE_NUTRITION_PROMPT,
    GENERATE_STEPS_PROMPT,
    SUGGEST_DISHES_PROMPT,
)
from .schemas import (
    DishSuggestions,
    RecipeIngredients,
    RecipeMetadata,
    RecipeNutrition,
    RecipeSteps,
    RequestAnalysis,
)

logger = logging.getLogger(__name__)


class RecipeCreatorState(TypedDict):
    """State for the recipe creator graph"""

    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    user_message: str

    # Recipe data (progressively filled)
    name: Optional[str]
    description: Optional[str]
    difficulty: Optional[str]
    total_time_minutes: Optional[int]
    servings: Optional[int]
    tags: Optional[List[str]]
    ingredients: Optional[List[dict]]
    steps: Optional[List[dict]]
    nutrition: Optional[dict]

    # Control flow
    intent: Optional[Literal["recipe", "modify", "suggest", "question"]]
    recipe_request: Optional[str]
    modification_request: Optional[str]
    what_to_modify: Optional[List[str]]
    text_response: Optional[str]
    generation_complete: bool


@dataclass
class RecipeEvent:
    """Event emitted during recipe generation"""

    type: Literal[
        "text",
        "thinking",
        "session_name",
        "metadata",
        "ingredients",
        "steps",
        "nutrition",
        "complete",
    ]
    data: Any


# Thinking messages for each generation node
THINKING_MESSAGES = {
    "gen_metadata": "Setting up recipe",
    "gen_ingredients": "Generating ingredients",
    "gen_steps": "Writing steps",
    "gen_nutrition": "Calculating nutrition",
    "modify": "Updating recipe",
}


class RecipeCreatorAgent:
    """Agent for recipe creation with structured output generation"""

    MODEL = "gpt-4o-mini"

    def __init__(self):
        """Initialize the recipe creator agent"""
        self.llm = ChatOpenAI(
            model=self.MODEL,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        logger.info(f"🤖 RecipeCreatorAgent using model: {self.MODEL}")
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with sequential generation"""
        workflow = StateGraph(RecipeCreatorState)

        # Add nodes
        workflow.add_node("analyze", self._analyze_request)
        workflow.add_node("suggest", self._suggest_dishes)
        workflow.add_node("ask", self._ask_question)
        workflow.add_node("check", self._check_completeness)
        workflow.add_node("modify", self._modify_recipe)
        workflow.add_node("gen_metadata", self._generate_metadata)
        workflow.add_node("gen_ingredients", self._generate_ingredients)
        workflow.add_node("gen_steps", self._generate_steps)
        workflow.add_node("gen_nutrition", self._generate_nutrition)
        workflow.add_node("final", self._final_response)

        # Entry point
        workflow.set_entry_point("analyze")

        # Route from analyze based on intent
        workflow.add_conditional_edges(
            "analyze",
            self._route_intent,
            {"suggest": "suggest", "question": "ask", "recipe": "check", "modify": "modify"},
        )

        # Suggest and ask both end
        workflow.add_edge("suggest", END)
        workflow.add_edge("ask", END)

        # Modify routes back to check for regeneration
        workflow.add_edge("modify", "check")

        # Check routes to generation or final
        workflow.add_conditional_edges(
            "check",
            self._route_generation,
            {"generate": "gen_metadata", "complete": "final"},
        )

        # Sequential generation: metadata → ingredients → steps → nutrition
        workflow.add_edge("gen_metadata", "gen_ingredients")
        workflow.add_edge("gen_ingredients", "gen_steps")
        workflow.add_edge("gen_steps", "gen_nutrition")

        # After nutrition, check completeness (for fallback loop)
        workflow.add_edge("gen_nutrition", "check")

        # Final response ends
        workflow.add_edge("final", END)

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

    def _format_existing_recipe(self, state: RecipeCreatorState) -> str:
        """Format existing recipe from state for prompts"""
        # Consider recipe as existing if it has name OR has content (ingredients/steps)
        has_name = bool(state.get("name"))
        has_content = bool(state.get("ingredients") or state.get("steps"))

        if not has_name and not has_content:
            return "(No recipe in session yet)"

        parts = []

        if state.get("name"):
            parts.append(f"Name: {state['name']}")
        elif has_content:
            # Recipe exists but name is missing (might have been cleared)
            parts.append("Name: (missing - needs to be restored)")

        if state.get("description"):
            parts.append(f"Description: {state['description']}")
        elif has_content and not state.get("description"):
            parts.append("Description: (missing)")

        if state.get("servings"):
            parts.append(f"Servings: {state['servings']}")

        if state.get("difficulty"):
            parts.append(f"Difficulty: {state['difficulty']}")
        elif has_content and not state.get("difficulty"):
            parts.append("Difficulty: (missing)")

        if state.get("total_time_minutes"):
            parts.append(f"Total time: {state['total_time_minutes']} minutes")
        elif has_content and not state.get("total_time_minutes"):
            parts.append("Total time: (missing)")

        if state.get("ingredients"):
            ing_names = [ing.get("name", "") for ing in state["ingredients"][:5]]
            parts.append(f"Key ingredients: {', '.join(ing_names)}...")

        if state.get("steps"):
            parts.append(f"Steps: {len(state['steps'])} steps defined")

        return "\n".join(parts)

    async def _analyze_request(self, state: RecipeCreatorState) -> Dict:
        """Analyze user request to determine intent"""
        message_history = self._format_message_history(state["messages"][:-1])
        existing_recipe = self._format_existing_recipe(state)

        prompt = ANALYZE_REQUEST_PROMPT.format(
            existing_recipe=existing_recipe,
            message_history=message_history,
            user_message=state["user_message"],
        )

        llm_with_output = self.llm.with_structured_output(RequestAnalysis)
        result: RequestAnalysis = await llm_with_output.ainvoke(prompt)

        logger.info(f"📊 Request analysis: intent={result.intent}")

        return {
            "intent": result.intent,
            "recipe_request": result.recipe_request,
            "modification_request": result.modification_request,
            "what_to_modify": result.what_to_modify,
            "text_response": result.text_response,
        }

    def _route_intent(self, state: RecipeCreatorState) -> str:
        """Route based on analyzed intent"""
        intent = state.get("intent")
        if intent == "suggest":
            return "suggest"
        if intent == "question":
            return "question"
        if intent == "modify":
            return "modify"
        return "recipe"

    async def _suggest_dishes(self, state: RecipeCreatorState) -> Dict:
        """Generate dish suggestions for the user"""
        message_history = self._format_message_history(state["messages"][:-1])

        prompt = SUGGEST_DISHES_PROMPT.format(
            message_history=message_history,
            user_message=state["user_message"],
        )

        llm_with_output = self.llm.with_structured_output(DishSuggestions)
        result: DishSuggestions = await llm_with_output.ainvoke(prompt)

        # Format suggestions as text
        suggestions_text = result.response_text + "\n\n"
        for i, suggestion in enumerate(result.suggestions, 1):
            suggestions_text += f"{i}. **{suggestion.name}** - {suggestion.description}\n"
        suggestions_text += "\nWhich one sounds good, or would you like different options?"

        logger.info(f"💡 Generated {len(result.suggestions)} dish suggestions")

        return {"text_response": suggestions_text}

    async def _ask_question(self, state: RecipeCreatorState) -> Dict:
        """Generate a clarifying question"""
        # If we already have a text_response from analysis, use it
        if state.get("text_response"):
            return {}

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = ASK_QUESTION_PROMPT.format(
            message_history=message_history,
            user_message=state["user_message"],
        )

        response = await self.llm.ainvoke(prompt)

        return {"text_response": response.content}

    async def _modify_recipe(self, state: RecipeCreatorState) -> Dict:
        """Clear parts of recipe that need regeneration for modification"""
        what_to_modify = state.get("what_to_modify") or []
        modification = state.get("modification_request", "")

        logger.info(f"🔄 Modifying recipe: {modification}, fields: {what_to_modify}")

        # Build recipe context - use name if available, otherwise indicate metadata restoration
        recipe_name = state.get("name")
        if recipe_name:
            recipe_context = f"{recipe_name} - {modification}" if modification else recipe_name
        elif state.get("ingredients") or state.get("steps"):
            # Recipe exists but name is missing - LLM will identify from ingredients/steps
            recipe_context = f"Restore metadata for existing recipe - {modification}" if modification else "Restore metadata for existing recipe"
        else:
            recipe_context = modification or "Recipe"

        updates: Dict[str, Any] = {
            "recipe_request": recipe_context,
            "generation_complete": False,
        }

        # Clear individual metadata fields
        if "name" in what_to_modify:
            updates["name"] = None
        if "description" in what_to_modify:
            updates["description"] = None
        if "difficulty" in what_to_modify:
            updates["difficulty"] = None
        if "time" in what_to_modify:
            updates["total_time_minutes"] = None
        if "servings" in what_to_modify:
            updates["servings"] = None
        if "tags" in what_to_modify:
            updates["tags"] = None

        # Clear content fields
        if "ingredients" in what_to_modify:
            updates["ingredients"] = None
        if "steps" in what_to_modify:
            updates["steps"] = None
        if "nutrition" in what_to_modify:
            updates["nutrition"] = None

        return updates

    def _route_generation(self, state: RecipeCreatorState) -> str:
        """Route to generation or final based on completeness"""
        if state.get("generation_complete"):
            return "complete"

        # Check if we have all required fields
        has_metadata = all([
            state.get("name"),
            state.get("description"),
            state.get("difficulty"),
            state.get("total_time_minutes"),
            state.get("servings"),
        ])
        has_ingredients = bool(state.get("ingredients"))
        has_steps = bool(state.get("steps"))
        has_nutrition = bool(state.get("nutrition"))

        if has_metadata and has_ingredients and has_steps and has_nutrition:
            return "complete"

        return "generate"

    async def _check_completeness(self, state: RecipeCreatorState) -> Dict:
        """Check if recipe generation is complete"""
        has_all = all([
            state.get("name"),
            state.get("ingredients"),
            state.get("steps"),
            state.get("nutrition"),
        ])

        if has_all:
            return {"generation_complete": True}
        return {"generation_complete": False}

    def _get_modification_context(self, state: RecipeCreatorState) -> str:
        """Get modification context for generation prompts"""
        modification = state.get("modification_request")
        if modification:
            return f"\nModification requested: {modification}"
        return ""

    async def _generate_metadata(self, state: RecipeCreatorState) -> Dict:
        """Generate recipe metadata (name, description, etc.) - supports partial regeneration"""
        # Check which metadata fields need generation
        needs_name = state.get("name") is None
        needs_desc = state.get("description") is None
        needs_diff = state.get("difficulty") is None
        needs_time = state.get("total_time_minutes") is None
        needs_serv = state.get("servings") is None
        needs_tags = state.get("tags") is None

        # Skip if nothing needs generation
        if not any([needs_name, needs_desc, needs_diff, needs_time, needs_serv, needs_tags]):
            return {}

        # Include existing content to help LLM identify the recipe when restoring metadata
        existing_content = ""
        if state.get("ingredients"):
            ing_text = "\n".join([
                f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing['name']}".strip()
                for ing in state["ingredients"]
            ])
            existing_content += f"\nEXISTING INGREDIENTS:\n{ing_text}"
        if state.get("steps"):
            step_text = "\n".join([
                f"{i}. {step.get('instruction', '')}"
                for i, step in enumerate(state["steps"][:5], 1)  # First 5 steps
            ])
            if len(state["steps"]) > 5:
                step_text += f"\n... and {len(state['steps']) - 5} more steps"
            existing_content += f"\n\nEXISTING STEPS:\n{step_text}"

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = GENERATE_METADATA_PROMPT.format(
            recipe_request=state.get("recipe_request") or state["user_message"],
            modification_context=self._get_modification_context(state),
            existing_content=existing_content,
            message_history=message_history,
        )

        llm_with_output = self.llm.with_structured_output(RecipeMetadata)
        result: RecipeMetadata = await llm_with_output.ainvoke(prompt)

        logger.info(f"📝 Generated metadata: {result.name} (partial={not needs_name})")

        # Only return fields that were actually None - preserve existing values
        updates: Dict[str, Any] = {}
        if needs_name:
            updates["name"] = result.name
        if needs_desc:
            updates["description"] = result.description
        if needs_diff:
            updates["difficulty"] = result.difficulty
        if needs_time:
            updates["total_time_minutes"] = result.total_time_minutes
        if needs_serv:
            updates["servings"] = result.servings
        if needs_tags:
            updates["tags"] = result.tags

        return updates

    async def _generate_ingredients(self, state: RecipeCreatorState) -> Dict:
        """Generate recipe ingredients"""
        # Skip if ingredients already exist - _modify_recipe clears when modification needed
        if state.get("ingredients"):
            return {}

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = GENERATE_INGREDIENTS_PROMPT.format(
            recipe_name=state.get("name", "Recipe"),
            recipe_description=state.get("description", ""),
            servings=state.get("servings", 4),
            modification_context=self._get_modification_context(state),
            message_history=message_history,
        )

        llm_with_output = self.llm.with_structured_output(RecipeIngredients)
        result: RecipeIngredients = await llm_with_output.ainvoke(prompt)

        logger.info(f"🥗 Generated {len(result.ingredients)} ingredients")

        return {
            "ingredients": [ing.model_dump() for ing in result.ingredients],
        }

    async def _generate_steps(self, state: RecipeCreatorState) -> Dict:
        """Generate recipe steps"""
        # Skip if steps already exist - _modify_recipe clears when modification needed
        if state.get("steps"):
            return {}

        # Format ingredients for prompt
        ingredients_text = ""
        if state.get("ingredients"):
            ingredients_text = "\n".join([
                f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing['name']}".strip()
                for ing in state["ingredients"]
            ])

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = GENERATE_STEPS_PROMPT.format(
            recipe_name=state.get("name", "Recipe"),
            recipe_description=state.get("description", ""),
            ingredients=ingredients_text or "Not yet generated",
            modification_context=self._get_modification_context(state),
            message_history=message_history,
        )

        llm_with_output = self.llm.with_structured_output(RecipeSteps)
        result: RecipeSteps = await llm_with_output.ainvoke(prompt)

        logger.info(f"📋 Generated {len(result.steps)} steps")

        return {
            "steps": [step.model_dump() for step in result.steps],
        }

    async def _generate_nutrition(self, state: RecipeCreatorState) -> Dict:
        """Generate nutrition information"""
        # Skip if nutrition already exists - _modify_recipe clears when modification needed
        if state.get("nutrition"):
            return {}

        # Format ingredients for prompt
        ingredients_text = ""
        if state.get("ingredients"):
            ingredients_text = "\n".join([
                f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing['name']}".strip()
                for ing in state["ingredients"]
            ])

        message_history = self._format_message_history(state["messages"][:-1])

        prompt = GENERATE_NUTRITION_PROMPT.format(
            recipe_name=state.get("name", "Recipe"),
            servings=state.get("servings", 4),
            ingredients=ingredients_text or "Not available",
            message_history=message_history,
        )

        llm_with_output = self.llm.with_structured_output(RecipeNutrition)
        result: RecipeNutrition = await llm_with_output.ainvoke(prompt)

        logger.info(f"🥗 Generated nutrition: {result.calories} cal")

        return {
            "nutrition": result.model_dump(),
        }

    async def _final_response(self, state: RecipeCreatorState) -> Dict:
        """Generate final text response after recipe is complete"""
        message_history = self._format_message_history(state["messages"][:-1])
        modification = state.get("modification_request")

        # Determine action description based on whether this was a modification
        if modification:
            action_description = f"modified the recipe ({modification})"
            modification_context = f"Modification made: {modification}"
        else:
            action_description = "created a new recipe"
            modification_context = ""

        prompt = FINAL_RESPONSE_PROMPT.format(
            action_description=action_description,
            recipe_name=state.get("name", "the recipe"),
            modification_context=modification_context,
            message_history=message_history,
            user_message=state["user_message"],
        )

        response = await self.llm.ainvoke(prompt)

        result = {"text_response": response.content}
        if modification:
            result["modification_request"] = None  # Clear the modification
        return result

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
    ) -> AsyncGenerator[RecipeEvent, None]:
        """
        Run the agent and yield events as recipe parts are generated.

        Args:
            message: User message to process
            message_history: Previous message history from database
            session_id: Session ID for context
            session_data: Full session data including existing recipe

        Yields:
            RecipeEvent for each generation step
        """
        # Convert message history and add new message
        langchain_messages = self._convert_message_history(message_history)
        langchain_messages.append(HumanMessage(content=message))

        logger.info(f"📚 Message history: {len(message_history)} messages, {len(langchain_messages)} converted")

        # Load existing recipe from session_data (handle None case)
        existing_recipe = session_data.get("recipe") or {}
        logger.info(f"📝 Existing recipe in session: name={existing_recipe.get('name')}, has_ingredients={bool(existing_recipe.get('ingredients'))}, has_steps={bool(existing_recipe.get('steps'))}")

        # Create initial state with existing recipe data
        initial_state: RecipeCreatorState = {
            "messages": langchain_messages,
            "session_id": session_id,
            "user_message": message,
            # Load existing recipe data
            "name": existing_recipe.get("name"),
            "description": existing_recipe.get("description"),
            "difficulty": existing_recipe.get("difficulty"),
            "total_time_minutes": existing_recipe.get("total_time_minutes"),
            "servings": existing_recipe.get("servings"),
            "tags": existing_recipe.get("tags"),
            "ingredients": existing_recipe.get("ingredients"),
            "steps": existing_recipe.get("steps"),
            "nutrition": existing_recipe.get("nutrition"),
            # Control flow
            "intent": None,
            "recipe_request": None,
            "modification_request": None,
            "what_to_modify": None,
            "text_response": None,
            "generation_complete": False,
        }

        message_id = f"msg-{uuid.uuid4()}"

        # Track what we've already yielded to avoid duplicates
        yielded_session_name = False
        yielded_metadata = False
        yielded_ingredients = False
        yielded_steps = False
        yielded_nutrition = False
        yielded_any_recipe_update = False  # Track if any recipe part was updated

        # Check if this is a new recipe (no existing name) - we'll send session_name for new recipes only
        is_new_recipe = not existing_recipe.get("name")

        # Track current metadata state (for partial updates, we need to emit all values)
        current_metadata = {
            "name": existing_recipe.get("name"),
            "description": existing_recipe.get("description"),
            "difficulty": existing_recipe.get("difficulty"),
            "total_time_minutes": existing_recipe.get("total_time_minutes"),
            "servings": existing_recipe.get("servings"),
            "tags": existing_recipe.get("tags"),
        }

        # Stream through the graph
        async for event in self.graph.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in event.items():
                # Skip if node returned None or empty dict
                if not state_update:
                    continue
                logger.debug(f"📦 Node '{node_name}' update: {list(state_update.keys())}")

                # Send thinking message for generation nodes
                if node_name in THINKING_MESSAGES:
                    yield RecipeEvent(type="thinking", data=THINKING_MESSAGES[node_name])

                # Emit events for state changes
                # Check for any metadata field updates (supports partial regeneration)
                metadata_fields = {"name", "description", "difficulty", "total_time_minutes", "servings", "tags"}
                updated_metadata = {k: v for k, v in state_update.items() if k in metadata_fields and v is not None}

                if updated_metadata:
                    yielded_any_recipe_update = True

                    # Update tracking dict with new values
                    current_metadata.update(updated_metadata)

                    # Send session_name event for new recipes (not modifications)
                    if is_new_recipe and not yielded_session_name and "name" in updated_metadata:
                        yielded_session_name = True
                        yield RecipeEvent(
                            type="session_name",
                            data=updated_metadata["name"],
                        )

                    # For full metadata generation, emit all fields at once
                    # For partial updates, emit only the updated fields
                    if not yielded_metadata and len(updated_metadata) == len(metadata_fields):
                        yielded_metadata = True

                    # Emit all non-null metadata values (existing + updated)
                    # This ensures UI always gets complete metadata state
                    emit_metadata = {k: v for k, v in current_metadata.items() if v is not None}
                    yield RecipeEvent(
                        type="metadata",
                        data=emit_metadata,
                    )

                if not yielded_ingredients and state_update.get("ingredients"):
                    yielded_ingredients = True
                    yielded_any_recipe_update = True
                    yield RecipeEvent(
                        type="ingredients",
                        data=state_update["ingredients"],
                    )

                if not yielded_steps and state_update.get("steps"):
                    yielded_steps = True
                    yielded_any_recipe_update = True
                    yield RecipeEvent(
                        type="steps",
                        data=state_update["steps"],
                    )

                if not yielded_nutrition and state_update.get("nutrition"):
                    yielded_nutrition = True
                    yielded_any_recipe_update = True
                    yield RecipeEvent(
                        type="nutrition",
                        data=state_update["nutrition"],
                    )

                # Text responses (chat, clarification, or final)
                if state_update.get("text_response"):
                    yield RecipeEvent(
                        type="text",
                        data={
                            "content": state_update["text_response"],
                            "message_id": message_id,
                        },
                    )

        # Send completion if we generated or modified a recipe
        if yielded_any_recipe_update:
            yield RecipeEvent(type="complete", data=None)
