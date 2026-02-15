"""
Raimy Agent Service

FastAPI service for chat agent orchestration with LangGraph.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.services import database_service
from agents import get_agent
from agents.recipe_creator.agent import RecipeCreatorAgent
from agents.kitchen.agent import KitchenAgent
from agents.memory import memory_agent
from core.redis_client import get_redis_client
from services.image_pipeline import StepImagePipeline

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Get Redis client for recipe creator events
redis_client = get_redis_client()

# FastAPI app
app = FastAPI(
    title="Raimy Agent Service",
    description="LangGraph-based agent service for chat and cooking assistance",
    version="3.0.0",
)

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
    message_id: Optional[str] = None
    session_id: str


class GreetingRequest(BaseModel):
    """Request model for greeting endpoint"""
    session_type: str
    recipe_name: Optional[str] = None


class GreetingResponse(BaseModel):
    """Response model for greeting endpoint"""
    greeting: str
    message_type: str = "text"  # "text" or "kitchen-step"
    next_step_prompt: Optional[str] = None


class ExtractMemoryRequest(BaseModel):
    """Request model for memory extraction endpoint"""
    session_id: str
    user_id: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent", "version": "3.0.0"}


async def _extract_and_save_memory(
    user_id: str,
    session_id: str,
    messages: List[Dict[str, Any]],
) -> None:
    """
    Extract memory and save to DB. Called on session completion events.

    Args:
        user_id: User email
        session_id: Session ID for logging
        messages: Conversation messages from the session
    """
    try:
        current_memory = await database_service.get_user_memory(user_id)

        # memory_agent.extract() is now a pure function
        updated_memory = await memory_agent.extract(messages, current_memory)

        if updated_memory:
            await database_service.save_user_memory(user_id, updated_memory)
            logger.info(f"🧠 Memory updated for user {user_id}")
    except Exception as e:
        logger.error(f"🧠 Memory extraction failed: {e}", exc_info=True)


async def _generate_step_images(session_id: str, steps: list, recipe_name: str):
    """Background task: generate images for all recipe steps."""
    redis_client = get_redis_client()
    try:
        await redis_client.send_system_message(
            session_id, "thinking", "Generating step images..."
        )
        pipeline = StepImagePipeline()
        results = await pipeline.generate_step_images(session_id, steps, recipe_name)
        logger.info(f"Generated {len(results)} step images for session {session_id}")
    except Exception as e:
        logger.error(f"Step image generation failed: {e}", exc_info=True)
    finally:
        await redis_client.send_system_message(session_id, "thinking", None)


@app.post("/agent/greeting", response_model=GreetingResponse)
async def generate_greeting(request: GreetingRequest):
    """
    Generate a personalized greeting for a new session.

    Args:
        request: Contains session_type and optional recipe_name

    Returns:
        LLM-generated greeting with message type info
    """
    try:
        agent = await get_agent(session_type=request.session_type)

        if isinstance(agent, KitchenAgent):
            result = await agent.generate_greeting(recipe_name=request.recipe_name)
            logger.info(f"👋 Generated greeting for session_type={request.session_type}")
            return GreetingResponse(
                greeting=result["greeting"],
                message_type=result.get("message_type", "text"),
                next_step_prompt=result.get("next_step_prompt"),
            )
        elif isinstance(agent, RecipeCreatorAgent):
            greeting = await agent.generate_greeting()
            logger.info(f"👋 Generated greeting for session_type={request.session_type}")
            return GreetingResponse(greeting=greeting)
        else:
            # Fallback for unknown agent types
            return GreetingResponse(greeting="Hello! I'm here to help.")

    except Exception as e:
        logger.error(f"Error generating greeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_kitchen_events(
    agent: KitchenAgent,
    request: ChatRequest,
    messages: List[Dict],
    session_data: Dict,
) -> ChatResponse:
    """
    Handle kitchen agent events and convert them to Redis messages.

    Returns:
        ChatResponse with final text
    """
    text_response = ""
    message_id = None
    new_agent_state = None
    saved_content = None  # Track content for database save

    async for event in agent.run_streaming(
        message=request.message,
        message_history=messages,
        session_id=request.session_id,
        session_data=session_data,
    ):
        logger.debug(f"📤 Kitchen event: {event.type}")

        match event.type:
            case "thinking":
                await redis_client.send_system_message(
                    request.session_id, "thinking", event.data
                )

            case "ingredients_highlight":
                # Update ingredients in database
                await redis_client.send_ingredients_message(
                    request.session_id,
                    items=event.data,
                    action="update",
                )

            case "timer":
                await redis_client.send_timer_message(
                    request.session_id,
                    duration=event.data["duration"],
                    label=event.data["label"],
                )

            case "session_name":
                await redis_client.send_session_name_message(
                    request.session_id, event.data
                )

            case "recipe_created":
                # Save full recipe to session
                recipe = event.data
                await database_service.save_session_recipe(
                    request.session_id, recipe
                )
                logger.info(f"📝 Saved recipe to session: {recipe.get('name')}")

            case "ingredients_set":
                # Set initial cooking ingredients
                await redis_client.send_ingredients_message(
                    request.session_id,
                    items=event.data,
                    action="set",
                )

            case "agent_state":
                # Store for persistence after loop
                new_agent_state = event.data

            case "kitchen_step":
                # Step guidance with prompt button
                message = event.data.get("message", "")
                message_id = event.data.get("message_id")
                next_step_prompt = event.data.get("next_step_prompt", "Continue")
                text_response = message
                # Track content for database save
                saved_content = {
                    "type": "kitchen-step",
                    "message": message,
                    "next_step_prompt": next_step_prompt,
                }
                await redis_client.send_kitchen_step_message(
                    request.session_id, message, message_id, next_step_prompt
                )

            case "text":
                text_response = event.data.get("content", "")
                message_id = event.data.get("message_id")
                # Track content for database save (regular text)
                saved_content = {"type": "text", "content": text_response}
                await redis_client.send_agent_text_message(
                    request.session_id, text_response, message_id
                )

            case "selector":
                message = event.data.get("message", "")
                options = event.data.get("options", [])
                message_id = event.data.get("message_id")
                text_response = message
                saved_content = {
                    "type": "selector",
                    "message": message,
                    "options": options,
                }
                logger.debug(f"🎯 Kitchen selector: {len(options)} options")
                await redis_client.send_selector_message(
                    request.session_id, message, options, message_id
                )

            case "cooking_complete":
                # Mark session as finished
                await database_service.mark_session_finished(request.session_id)

                # Send cooking_complete message to frontend
                await redis_client.send_cooking_complete_message(request.session_id)

                # Trigger memory extraction
                user_id = session_data.get("user_id")
                if user_id:
                    # Get updated messages from DB
                    full_messages = messages + [
                        {"role": "user", "content": {"type": "text", "content": request.message}},
                    ]
                    if saved_content:
                        full_messages.append({"role": "assistant", "content": saved_content})

                    asyncio.create_task(
                        _extract_and_save_memory(user_id, request.session_id, full_messages)
                    )

            case "complete":
                await redis_client.send_system_message(
                    request.session_id, "thinking", None
                )

    # Save agent response to database with correct content type
    if saved_content:
        logger.debug(f"💾 Kitchen saving to DB: type={saved_content.get('type')}")
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="assistant",
            content=saved_content,
        )

    # Persist agent state if changed
    if new_agent_state is not None:
        await database_service.update_agent_state(
            request.session_id,
            new_agent_state,
        )

    return ChatResponse(
        response=text_response or "I'm here to help you cook!",
        message_id=message_id,
        session_id=request.session_id,
    )


async def _handle_recipe_creator_events(
    agent: RecipeCreatorAgent,
    request: ChatRequest,
    messages: List[Dict],
    session_data: Dict,
) -> ChatResponse:
    """
    Handle recipe creator agent events and convert them to Redis messages.

    Returns:
        ChatResponse with final text and structured outputs
    """
    text_response = ""
    message_id = None
    recipe_data = {}
    saved_content = None  # Track content for database save

    async for event in agent.run_streaming(
        message=request.message,
        message_history=messages,
        session_id=request.session_id,
        session_data=session_data,
    ):
        logger.debug(f"📤 Recipe event: {event.type}")

        match event.type:
            case "thinking":
                await redis_client.send_system_message(
                    request.session_id, "thinking", event.data
                )

            case "session_name":
                await redis_client.send_session_name_message(
                    request.session_id, event.data
                )

            case "metadata":
                recipe_data.update(event.data)
                await redis_client.send_recipe_metadata_message(
                    request.session_id,
                    name=event.data.get("name"),
                    description=event.data.get("description"),
                    difficulty=event.data.get("difficulty"),
                    total_time_minutes=event.data.get("total_time_minutes"),
                    servings=event.data.get("servings"),
                    tags=event.data.get("tags"),
                )

            case "ingredients":
                recipe_data["ingredients"] = event.data
                await redis_client.send_recipe_ingredients_message(
                    request.session_id, event.data
                )

            case "steps":
                recipe_data["steps"] = event.data
                await redis_client.send_recipe_steps_message(
                    request.session_id, event.data
                )

            case "nutrition":
                recipe_data["nutrition"] = event.data
                await redis_client.send_recipe_nutrition_message(
                    request.session_id, event.data
                )

            case "text":
                text_response = event.data.get("content", "")
                message_id = event.data.get("message_id")
                saved_content = {"type": "text", "content": text_response}
                await redis_client.send_agent_text_message(
                    request.session_id, text_response, message_id
                )

            case "selector":
                message = event.data.get("message", "")
                options = event.data.get("options", [])
                message_id = event.data.get("message_id")
                text_response = message
                saved_content = {
                    "type": "selector",
                    "message": message,
                    "options": options,
                }
                logger.debug(f"🎯 Recipe selector: {len(options)} options")
                await redis_client.send_selector_message(
                    request.session_id, message, options, message_id
                )

            case "complete":
                # Clear thinking indicator
                await redis_client.send_system_message(
                    request.session_id, "thinking", None
                )

                # Trigger image generation in background
                if recipe_data.get("steps"):
                    asyncio.create_task(
                        _generate_step_images(
                            session_id=request.session_id,
                            steps=recipe_data["steps"],
                            recipe_name=recipe_data.get("name", "Recipe"),
                        )
                    )

    # Save agent response to database with correct content type
    if saved_content:
        logger.debug(f"💾 Saving to DB: type={saved_content.get('type')}")
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="assistant",
            content=saved_content,
        )

    # Recipe data is already persisted via Redis → app/main.py → database_service
    return ChatResponse(
        response=text_response or "I'm here to help with recipes!",
        message_id=message_id,
        session_id=request.session_id,
    )


@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    Chat endpoint that processes messages using LangGraph agent.

    Steps:
    1. Load session context from database
    2. Get appropriate agent based on session type
    3. Run agent to generate response
    4. Save messages to database
    5. Return agent response
    """
    try:
        # Get session from database
        session_data = await database_service.get_chat_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Extract session info
        messages = session_data.get("messages", [])
        session_type = session_data.get("session_type", "recipe-creator")

        # Log if we have a recipe in session (saved via Redis → database flow)
        if session_data.get("recipe"):
            logger.info(f"📝 Found existing recipe in session: {session_data['recipe'].get('name')}")

        # Load recipe data if recipe_id is present (for kitchen sessions)
        recipe_id = session_data.get("recipe_id")
        if recipe_id:
            logger.info(f"🍳 Loading recipe {recipe_id} for kitchen session")
            recipe_data = await database_service.get_recipe_by_id(recipe_id)
            if recipe_data:
                session_data["recipe"] = recipe_data
                logger.info(f"✅ Loaded recipe: {recipe_data.get('name')}")
            else:
                logger.error(f"❌ Recipe {recipe_id} not found")

        # Load user memory for context
        user_id = session_data.get("user_id")
        if user_id:
            user_memory = await database_service.get_user_memory(user_id)
            if user_memory:
                session_data["user_memory"] = user_memory
                logger.info(f"🧠 Loaded user memory for {user_id}")

        # Save user message to database
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="user",
            content={"type": "text", "content": request.message},
        )

        # Get agent for this session type (cached)
        agent = await get_agent(session_type=session_type)

        # Handle agents with generator streaming
        if isinstance(agent, RecipeCreatorAgent):
            return await _handle_recipe_creator_events(
                agent, request, messages, session_data
            )

        if isinstance(agent, KitchenAgent):
            return await _handle_kitchen_events(
                agent, request, messages, session_data
            )

        # Fallback for unknown agent types (shouldn't happen)
        raise HTTPException(status_code=500, detail=f"Unknown agent type: {type(agent)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent_chat: {e}", exc_info=True)

        # Publish error to Redis
        try:
            await redis_client.publish(
                f"session:{request.session_id}",
                {
                    "type": "system",
                    "content": {
                        "type": "error",
                        "message": "An error occurred processing your message",
                    },
                },
            )
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/extract-memory")
async def extract_memory_endpoint(request: ExtractMemoryRequest):
    """
    Trigger memory extraction for a session.

    Called by external services (e.g., save-recipe endpoint) when
    a session reaches a completion point.
    """
    session_data = await database_service.get_chat_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session_data.get("messages", [])

    # Run extraction in background
    asyncio.create_task(
        _extract_and_save_memory(request.user_id, request.session_id, messages)
    )

    return {"status": "extraction_started"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True, log_level="info")
