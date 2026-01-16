import os
import sys
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services import database_service  # type: ignore
from agents.prompts import COOKING_ASSISTANT_PROMPT, RECIPE_CREATOR_PROMPT  # type: ignore
from agents import KitchenAgent, RecipeCreatorAgent  # type: ignore
from agents.base_agent import BaseAgent  # type: ignore
from agents.mcp_tools import load_mcp_tools_for_langchain  # type: ignore

load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

# Cache of agent instances by session type
agent_instances: Dict[str, BaseAgent] = {}


def format_recipe_context(recipe_data: Dict[str, Any]) -> str:
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

    context += f"""
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


def calculate_current_step(recipe: Dict[str, Any], ingredients: List[Dict]) -> Optional[Dict]:
    """
    Calculate current step from recipe and ingredient state (kitchen mode only)

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
            ing.get("name", "") for ing in recipe_ingredients
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
                "tools_called": []
            }

    # All steps complete
    return None


async def get_agent(session_type: str = "recipe-creator") -> BaseAgent:
    """
    Get or create agent instance for the specified session type

    Args:
        session_type: Session type ("kitchen" or "recipe-creator")

    Returns:
        Agent instance (KitchenAgent or RecipeCreatorAgent) with session-type-specific tools
    """
    global agent_instances

    # Validate session_type and default to recipe-creator if unknown
    if session_type not in {"kitchen", "recipe-creator"}:
        logger.warning(f"⚠️  Unknown session_type '{session_type}', defaulting to 'recipe-creator'")
        session_type = "recipe-creator"

    # Return cached instance if exists
    if session_type in agent_instances:
        return agent_instances[session_type]

    # Create new agent instance with filtered tools
    logger.info(f"🔄 Creating new agent instance for session_type='{session_type}'")
    mcp_tools = await load_mcp_tools_for_langchain(session_type=session_type)

    if session_type == "kitchen":
        agent = KitchenAgent(mcp_tools=mcp_tools)
    else:  # recipe-creator
        agent = RecipeCreatorAgent(mcp_tools=mcp_tools)

    agent_instances[session_type] = agent

    logger.info(f"✅ Initialized {type(agent).__name__} for '{session_type}' with {len(mcp_tools)} tools")
    return agent


# FastAPI app
app = FastAPI(
    title="Raimy Agent Service",
    description="LangGraph-based agent service for chat and cooking assistance",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    structured_outputs: List[Dict] = []  # Recipe messages and other structured data
    message_id: Optional[str] = None
    session_id: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent",
        "version": "2.0.0"
    }


@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    Chat endpoint that processes messages using LangGraph agent

    Steps:
    1. Load session context from database
    2. Add user message to context (if not empty session auto-greeting)
    3. Run LangGraph agent to generate response
    4. Save both user message and agent response to database
    5. Return agent response
    """
    try:
        # Get session from database
        session_data = await database_service.get_chat_session(request.session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Extract message history
        messages = session_data.get("messages", [])

        # Read session type from database
        session_type = session_data.get("session_type", "recipe-creator")

        # Extract ingredients if present
        ingredients = session_data.get("ingredients", [])

        # Check for recipe_id and load recipe data
        recipe_id = session_data.get("recipe_id")
        recipe_data = None
        recipe_name = None

        if recipe_id:
            logger.info(f"🍳 Loading recipe {recipe_id} for kitchen session")
            recipe_data = await database_service.get_recipe_by_id(recipe_id)
            if recipe_data:
                recipe_name = recipe_data.get("name")
                logger.info(f"✅ Loaded recipe: {recipe_name}")
            else:
                logger.error(f"❌ Recipe {recipe_id} not found")

        # Select appropriate prompt based on session type
        if session_type == "kitchen":
            system_prompt = COOKING_ASSISTANT_PROMPT

            # Add recipe context if recipe_id was provided
            if recipe_data:
                recipe_context = format_recipe_context(recipe_data)
                system_prompt = system_prompt + "\n\n" + recipe_context

            # If resuming session with ingredients, add context
            if ingredients:
                ingredient_context = "\n\n**CURRENT SESSION STATE:**\n"
                ingredient_context += f"Ingredients for this recipe ({len(ingredients)} total):\n"
                for ing in ingredients:
                    status = ""
                    if ing.get("used"):
                        status = " [USED]"
                    elif ing.get("highlighted"):
                        status = " [CURRENTLY USING]"
                    ingredient_context += f"- {ing['name']}: {ing.get('amount', '')} {ing.get('unit', '')}{status}\n"
                ingredient_context += "\nContinue guiding from where the session left off.\n"
                system_prompt = system_prompt + ingredient_context

        elif session_type == "recipe-creator":
            system_prompt = RECIPE_CREATOR_PROMPT
        else:
            # Default to recipe-creator for unknown types
            system_prompt = RECIPE_CREATOR_PROMPT

        # Save user message to database first (as structured TextContent)
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="user",
            content={"type": "text", "content": request.message}
        )

        # Get LangGraph agent instance with session-type-specific tools
        agent = await get_agent(session_type=session_type)

        # Calculate current step for kitchen mode (enables tool deduplication)
        current_step = None
        if session_type == "kitchen" and recipe_data:
            current_step = calculate_current_step(recipe_data, ingredients)
            if current_step:
                logger.debug(f"📍 Current step: {current_step.get('index')} - {current_step.get('instruction')[:50]}...")

        # Run agent with streaming to generate response
        # Kitchen agent accepts current_step, recipe-creator does not
        if session_type == "kitchen":
            agent_result = await agent.run_streaming(
                message=request.message,
                message_history=messages,
                system_prompt=system_prompt,
                session_id=request.session_id,
                current_step=current_step
            )
        else:
            agent_result = await agent.run_streaming(
                message=request.message,
                message_history=messages,
                system_prompt=system_prompt,
                session_id=request.session_id
            )

        # Extract response and structured outputs
        agent_response = agent_result["response"]
        structured_outputs = agent_result.get("structured_outputs", [])

        # Save agent text response to database (as structured TextContent)
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="assistant",
            content={"type": "text", "content": agent_response}
        )

        # If there are saved recipes, create structured messages for each
        for recipe_data in structured_outputs:
            # Transform recipe data into frontend-compatible format
            recipe_message = {
                "type": "recipe",
                "recipe_id": recipe_data.get("recipe_id"),
                "name": recipe_data.get("name"),
                "description": recipe_data.get("description"),
                "ingredients": [
                    {"name": ing} for ing in recipe_data.get("ingredients", [])
                ],
                "steps": [
                    {
                        "step_number": i + 1,
                        "instruction": step.get("instruction", ""),
                        "duration_minutes": step.get("duration_minutes")
                    }
                    for i, step in enumerate(recipe_data.get("steps", []))
                ],
                "total_time_minutes": recipe_data.get("total_time_minutes"),
                "difficulty": recipe_data.get("difficulty"),
                "servings": recipe_data.get("servings"),
                "tags": recipe_data.get("tags", [])
            }

            # Save structured recipe message to database
            await database_service.add_message_to_session(
                session_id=request.session_id,
                role="assistant",
                content=recipe_message
            )

        return ChatResponse(
            response=agent_response,
            structured_outputs=structured_outputs,
            session_id=request.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent_chat: {e}", exc_info=True)

        # Publish error to Redis so UI knows
        try:
            from core.redis_client import get_redis_client
            redis = get_redis_client()
            await redis.publish(
                f"session:{request.session_id}",
                {
                    "type": "system",
                    "content": {
                        "type": "error",
                        "message": "An error occurred processing your message"
                    }
                }
            )
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")

        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )