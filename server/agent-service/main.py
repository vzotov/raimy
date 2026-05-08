"""
Raimy Agent Service

FastAPI service for chat agent orchestration with LangGraph.
"""
import asyncio
import logging
import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.services import database_service
from agents import get_agent
from agents.unified.agent import UnifiedAgent
from agents.memory import memory_agent
from core.redis_client import get_redis_client

load_dotenv()

_IMAGE_GEN_ENABLED = bool(os.getenv("IMAGE_GEN_ENABLED"))
if _IMAGE_GEN_ENABLED:
    from agents.image_gen import ImageGenAgent
    from services.gcs_storage import GCSStorage

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
    message_already_saved: bool = False


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


class GenerateStepImageRequest(BaseModel):
    """Request model for single-step image generation"""
    recipe_name: str
    recipe_description: str = ""
    ingredients_summary: str = ""
    step_index: int
    step_instruction: str
    image_description: str = ""


class GenerateStepImageResponse(BaseModel):
    """Response model for single-step image generation"""
    image_url: str
    step_index: int


class ExtractMemoryRequest(BaseModel):
    """Request model for memory extraction endpoint"""
    session_id: str
    user_id: str


class SuggestionsRequest(BaseModel):
    """Request model for home-page suggestion chips"""
    user_memory: Optional[str] = None
    recent_sessions: List[str] = []
    time_of_day: str = "morning"


class SuggestionsResponse(BaseModel):
    """Response model for home-page suggestion chips"""
    suggestions: List[str]


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


async def _generate_step_images(session_id: str, recipe_data: dict):
    """Background task: generate images for all recipe steps using ImageGenAgent."""
    redis_client = get_redis_client()
    gcs = GCSStorage()
    try:
        await redis_client.send_system_message(
            session_id, "thinking", "Generating step images..."
        )
        agent = ImageGenAgent()
        count = 0
        async for event in agent.run_streaming(
            message="",
            message_history=[],
            session_id=session_id,
            session_data={"recipe": recipe_data},
        ):
            if event.type == "step_image":
                data = event.data
                logger.info(f'📸 Received step image data for step {data["step_index"]}')
                if data.get("image_bytes"):
                    # Cache miss — upload to GCS and save to DB cache
                    image_url = gcs.upload_image(
                        data["image_bytes"], data["prompt"], 512, 512
                    )
                    await database_service.save_step_image_cache(
                            normalized_text=data["prompt"].lower().strip(),
                            embedding=data["embedding"],
                            image_url=image_url,
                            aspect_ratio="1:1",
                            prompt=data["prompt"],
                            model=data.get("model_used", ""),
                            generation_time_ms=data.get("generation_time_ms", 0),
                        )
                else:
                    # Cache hit
                    image_url = data["image_url"]
                await redis_client.send_step_image_message(
                    session_id, data["step_index"], image_url
                )
                count += 1
        logger.info(f"Generated {count} step images for session {session_id}")
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
        result = await agent.generate_greeting(recipe_name=request.recipe_name)
        logger.info(f"👋 Generated greeting for session_type={request.session_type}")
        return GreetingResponse(
            greeting=result["greeting"],
            message_type=result.get("message_type", "text"),
            next_step_prompt=result.get("next_step_prompt"),
        )

    except Exception as e:
        logger.error(f"Error generating greeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_unified_events(
    agent: UnifiedAgent,
    request: ChatRequest,
    messages: List[Dict],
    session_data: Dict,
) -> ChatResponse:
    """
    Handle unified agent events and convert them to Redis messages.

    Returns:
        ChatResponse with final text
    """
    text_response = ""
    message_id = None
    new_agent_state = None
    saved_content = None

    async for event in agent.run_streaming(
        message=request.message,
        message_history=messages,
        session_id=request.session_id,
        session_data=session_data,
    ):
        logger.debug(f"📤 Unified event: {event.type}")

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
                await redis_client.send_recipe_ingredients_message(
                    request.session_id, event.data
                )

            case "steps":
                await redis_client.send_recipe_steps_message(
                    request.session_id, event.data
                )

            case "nutrition":
                await redis_client.send_recipe_nutrition_message(
                    request.session_id, event.data
                )

            case "recipe_created":
                recipe = event.data
                await database_service.save_session_recipe(
                    request.session_id, recipe
                )
                logger.info(f"📝 Saved recipe to session: {recipe.get('name')}")

            case "agent_state":
                new_agent_state = event.data

            case "kitchen_step":
                message = event.data.get("message", "")
                message_id = event.data.get("message_id")
                next_step_prompt = event.data.get("next_step_prompt", "Continue")
                image_url = event.data.get("image_url")
                timer_minutes = event.data.get("timer_minutes")
                timer_label = event.data.get("timer_label")
                text_response = message
                saved_content = {
                    "type": "kitchen-step",
                    "message": message,
                    "next_step_prompt": next_step_prompt,
                }
                if image_url:
                    saved_content["image_url"] = image_url
                if timer_minutes is not None:
                    saved_content["timer_minutes"] = timer_minutes
                    saved_content["timer_label"] = timer_label
                await redis_client.send_kitchen_step_message(
                    request.session_id, message, message_id, next_step_prompt,
                    image_url=image_url,
                    timer_minutes=timer_minutes,
                    timer_label=timer_label,
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
                logger.debug(f"🎯 Selector: {len(options)} options")
                await redis_client.send_selector_message(
                    request.session_id, message, options, message_id
                )

            case "save_complete":
                # Trigger save via existing recipe_update flow in app/main.py
                await redis_client.send_recipe_save_request(request.session_id)
                logger.info(f"💾 Recipe save requested for session {request.session_id}")

            case "shopping_list":
                items = event.data.get("items", [])
                recipe_name = event.data.get("recipe_name", "")
                await redis_client.publish(
                    f"session:{request.session_id}",
                    {
                        "type": "agent_message",
                        "content": {
                            "type": "shopping_list",
                            "items": items,
                            "recipe_name": recipe_name,
                        },
                    },
                )
                logger.info(f"🛒 Shopping list sent: {len(items)} items")

            case "generate_images":
                existing_recipe = session_data.get("recipe") or {}
                if existing_recipe.get("steps"):
                    asyncio.create_task(
                        _generate_step_images(
                            session_id=request.session_id,
                            recipe_data=existing_recipe,
                        )
                    )

            case "cooking_complete":
                await database_service.mark_session_finished(request.session_id)
                await redis_client.send_cooking_complete_message(request.session_id)

                user_id = session_data.get("user_id")
                if user_id:
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

    if saved_content:
        logger.debug(f"💾 Saving to DB: type={saved_content.get('type')}")
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="assistant",
            content=saved_content,
        )

    if new_agent_state is not None:
        await database_service.update_agent_state(
            request.session_id,
            new_agent_state,
        )

    return ChatResponse(
        response=text_response or "I'm here to help!",
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
        session_type = session_data.get("session_type", "chat")

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

        if not request.message_already_saved:
            await database_service.add_message_to_session(
                session_id=request.session_id,
                role="user",
                content={"type": "text", "content": request.message},
            )

        # When the message was pre-saved (e.g. initial_message flow), strip it from
        # history so it doesn't appear twice in the LLM context (once in history,
        # once appended as the current message by run_streaming).
        messages_for_agent = messages[:-1] if request.message_already_saved else messages

        # Get agent for this session type (always UnifiedAgent)
        agent = await get_agent(session_type=session_type)

        return await _handle_unified_events(agent, request, messages_for_agent, session_data)

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


@app.post("/agent/generate-step-image", response_model=GenerateStepImageResponse)
async def generate_step_image(request: GenerateStepImageRequest):
    """Generate an image for a single recipe step."""
    if not os.getenv("IMAGE_GEN_ENABLED"):
        raise HTTPException(status_code=503, detail="Image generation is not enabled")

    try:
        agent = ImageGenAgent()
        image_url = await agent.generate_single_step_image(
            recipe_name=request.recipe_name,
            step_index=request.step_index,
            step_instruction=request.step_instruction,
            image_description=request.image_description,
            recipe_description=request.recipe_description,
            ingredients_summary=request.ingredients_summary,
        )

        if not image_url:
            raise HTTPException(status_code=500, detail="Image generation failed")

        return GenerateStepImageResponse(
            image_url=image_url,
            step_index=request.step_index,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🎨 Single step image generation failed: {e}", exc_info=True)
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


@app.post("/agent/suggestions", response_model=SuggestionsResponse)
async def generate_suggestions(request: SuggestionsRequest):
    """
    Generate personalized home-page suggestion chips.

    Uses user memory and recent session names to produce 4 short prompts
    the user can tap to start a new chat session.
    """
    _SUGGESTIONS_PROMPT = """You are a cooking assistant. Generate exactly 4 short, natural cooking prompt suggestions for a user to tap on the home page.

## User Profile
{user_memory}

## Recent Sessions (what they've cooked before)
{recent_sessions}

## Time of Day
{time_of_day}

## Instructions
- Each suggestion should be 3-8 words, natural and conversational
- Mix: something new to try, a classic comfort food, something quick, something seasonal or time-appropriate
- Avoid repeating recent sessions exactly; it's fine to offer variations
- Do NOT use quotes around the suggestions
- Return exactly 4 suggestions as a JSON array of strings

Examples of good suggestions:
- "Quick weeknight pasta carbonara"
- "Make a comforting chicken soup"
- "Something with the avocados I have"
- "Easy 20-minute stir fry"

Return JSON: {{"suggestions": ["...", "...", "...", "..."]}}"""

    from pydantic import BaseModel as PydanticBase
    class _Schema(PydanticBase):
        suggestions: List[str]

    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9)
        structured = llm.with_structured_output(_Schema)

        recent = "\n".join(f"- {s}" for s in request.recent_sessions[:5]) if request.recent_sessions else "None yet"
        memory = request.user_memory or "No profile yet"

        result = await structured.ainvoke(
            _SUGGESTIONS_PROMPT.format(
                user_memory=memory,
                recent_sessions=recent,
                time_of_day=request.time_of_day,
            )
        )
        suggestions = result.suggestions[:4]
        logger.info(f"💡 Generated {len(suggestions)} suggestions")
        return SuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        logger.warning(f"💡 Suggestions LLM failed, using fallback: {e}")
        fallbacks = {
            "morning": ["Quick breakfast eggs Benedict", "Make a smoothie bowl", "Easy overnight oats", "Fluffy pancakes from scratch"],
            "afternoon": ["Light chicken Caesar salad", "Quick avocado toast lunch", "Make a grain bowl", "Easy turkey wrap"],
            "evening": ["Cozy pasta carbonara tonight", "Quick weeknight stir fry", "Make a hearty soup", "Easy sheet pan dinner"],
        }
        return SuggestionsResponse(suggestions=fallbacks.get(request.time_of_day, fallbacks["evening"]))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True, log_level="info")
