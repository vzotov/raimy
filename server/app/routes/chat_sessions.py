from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
import asyncio
import logging
import os
from typing import List

import httpx

from ..services import database_service, RecipeModel, RecipeStepModel, RecipeIngredientModel
from .models import UpdateSessionNameRequest, CreateSessionRequest
from core.auth_client import auth_client

logger = logging.getLogger(__name__)

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8003")

async def get_current_user_with_storage(request: Request):
    """Get current user and ensure user data is stored in database"""
    try:
        # Verify authentication
        auth_data = await auth_client.verify_auth(request)

        if not auth_data.get("authenticated"):
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = auth_data.get("user", {})

        # Store/update user data in database
        if user_data and user_data.get('email'):
            try:
                await database_service.save_user(user_data)
                logger.debug(f"Updated user data for: {user_data.get('email')}")
            except Exception as e:
                logger.warning(f"Failed to store user data: {str(e)}")

        return user_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication error")

# Broadcast function will be injected
broadcast_event = None

router = APIRouter(prefix="/api/chat-sessions", tags=["chat_sessions"])


@router.post("")
async def create_session(
    request: CreateSessionRequest = None,
    current_user: dict = Depends(get_current_user_with_storage)
):
    """Create a new chat session"""
    try:
        session_type = request.session_type if request else "recipe-creator"
        recipe_id = request.recipe_id if request else None
        initial_message = request.initial_message if request else None
        session = await database_service.create_chat_session(
            current_user["email"],
            session_type,
            recipe_id,
            initial_message,
        )

        return {
            "message": "Session created successfully",
            "session": session
        }
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("")
async def list_sessions(
    session_type: str = None,
    current_user: dict = Depends(get_current_user_with_storage)
):
    """Get all sessions for the current user, optionally filtered by session_type (recipe-creator or kitchen)"""
    try:
        sessions = await database_service.get_user_chat_sessions(
            current_user["email"],
            session_type=session_type
        )
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/{session_id}")
async def get_session(session_id: str, current_user: dict = Depends(get_current_user_with_storage)):
    """Get a specific chat session with full message history"""
    try:
        session = await database_service.get_chat_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify ownership
        if session["user_id"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return {"session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.put("/{session_id}/name")
async def update_session_name(
    session_id: str,
    request: UpdateSessionNameRequest,
    current_user: dict = Depends(get_current_user_with_storage)
):
    """Update the name of a chat session"""
    try:
        # First verify session exists and user owns it
        session = await database_service.get_chat_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session["user_id"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update the name
        success = await database_service.update_session_name(session_id, request.session_name)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session name")

        return {
            "message": "Session name updated successfully",
            "session_id": session_id,
            "session_name": request.session_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session name: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update session name: {str(e)}")


async def _trigger_memory_extraction(session_id: str, user_id: str):
    """Fire-and-forget memory extraction via agent-service."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{AGENT_SERVICE_URL}/agent/extract-memory",
                json={"session_id": session_id, "user_id": user_id},
                timeout=5.0
            )
            logger.info(f"🧠 Triggered memory extraction for session {session_id}")
        except Exception as e:
            logger.warning(f"🧠 Memory extraction trigger failed: {e}")


@router.post("/{session_id}/save-recipe")
async def save_recipe_from_session(
    session_id: str,
    current_user: dict = Depends(get_current_user_with_storage)
):
    """
    Save the recipe from session.recipe JSON to the recipes table.

    This reads the work-in-progress recipe from session.recipe and creates
    a permanent recipe record. If session.recipe_id exists, it updates the
    existing recipe instead of creating a new one.
    """
    logger.info(f"🔵 API ENDPOINT: save_recipe_from_session called for session_id={session_id}")
    logger.info(f"🔵 API: Current user email={current_user.get('email')}")

    try:
        # Get session and verify ownership
        session_data = await database_service.get_chat_session(session_id)

        if not session_data:
            logger.error(f"❌ API: Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        # Authorization check
        is_service_account = current_user.get("email") == "service@raimy.internal"
        logger.info(f"🔍 API: is_service_account={is_service_account}")

        if not is_service_account and session_data["user_id"] != current_user["email"]:
            logger.error(f"❌ API: User {current_user['email']} not authorized for session owned by {session_data['user_id']}")
            raise HTTPException(status_code=403, detail="Not authorized")

        if is_service_account:
            logger.info(f"🔓 API: Service account access granted for session owned by {session_data['user_id']}")

        # Use shared database service method
        result = await database_service.save_recipe_from_session_data(session_id)

        # Trigger memory extraction (fire-and-forget)
        asyncio.create_task(
            _trigger_memory_extraction(session_id, session_data["user_id"])
        )

        return {
            "message": "Recipe saved successfully",
            **result
        }

    except HTTPException:
        raise
    except ValueError as e:
        # ValueError from database service indicates bad request (missing fields, etc.)
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save recipe from session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


@router.post("/{session_id}/steps/{step_index}/generate-image")
async def generate_step_image(
    session_id: str,
    step_index: int,
    current_user: dict = Depends(get_current_user_with_storage),
):
    """Generate an image for a single recipe step via agent service."""
    # Load session and verify ownership
    session_data = await database_service.get_chat_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_data["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")

    recipe = session_data.get("recipe")
    if not recipe:
        raise HTTPException(status_code=400, detail="Session has no recipe")

    steps = recipe.get("steps", [])
    if step_index < 0 or step_index >= len(steps):
        raise HTTPException(status_code=400, detail="Invalid step index")

    step = steps[step_index]

    # Build recipe context
    ingredients = recipe.get("ingredients", [])
    ingredients_summary = ", ".join(
        ing.get("name", "") for ing in ingredients[:10]
    )
    if len(ingredients) > 10:
        ingredients_summary += f" (+{len(ingredients) - 10} more)"

    # Call agent service
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/agent/generate-step-image",
                json={
                    "recipe_name": recipe.get("name", "Recipe"),
                    "recipe_description": recipe.get("description", ""),
                    "ingredients_summary": ingredients_summary or "Not specified",
                    "step_index": step_index,
                    "step_instruction": step.get("instruction", ""),
                    "image_description": step.get("image_description", ""),
                },
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as e:
        detail = "Image generation service error"
        if e.response.status_code == 503:
            detail = "Image generation is not enabled"
        logger.error(f"Agent service error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Failed to call agent service for step image: {e}")
        raise HTTPException(status_code=500, detail="Image generation failed")

    # Update session recipe in DB
    image_url = result["image_url"]
    await database_service.update_step_image_url(session_id, step_index, image_url)

    return {"image_url": image_url, "step_index": step_index}


@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user_with_storage)):
    """Delete a chat session"""
    try:
        # First verify session exists and user owns it
        session = await database_service.get_chat_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session["user_id"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete the session
        success = await database_service.delete_chat_session(session_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")

        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/home-suggestions")
async def get_home_suggestions(current_user: dict = Depends(get_current_user_with_storage)):
    """
    Return 4 personalized suggestion chips for the home page.
    Calls agent service with user memory + recent session names.
    Falls back gracefully if agent service is unavailable.
    """
    user_id = current_user["email"]

    # Determine time of day bucket
    hour = datetime.now(timezone.utc).hour
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    # Fetch user memory and recent sessions in parallel
    try:
        user_memory, sessions = await asyncio.gather(
            database_service.get_user_memory(user_id),
            database_service.get_user_chat_sessions(user_id, session_type="chat"),
        )
    except Exception as e:
        logger.warning(f"Failed to load user context for suggestions: {e}")
        user_memory = None
        sessions = []

    recent_names = [s["session_name"] for s in sessions[:5] if s.get("session_name")]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{AGENT_SERVICE_URL}/agent/suggestions",
                json={
                    "user_memory": user_memory,
                    "recent_sessions": recent_names,
                    "time_of_day": time_of_day,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"suggestions": data.get("suggestions", [])}
    except Exception as e:
        logger.warning(f"💡 Agent suggestions failed, using fallback: {e}")
        fallbacks = {
            "morning": ["Quick breakfast eggs Benedict", "Make a smoothie bowl", "Easy overnight oats", "Fluffy pancakes from scratch"],
            "afternoon": ["Light chicken Caesar salad", "Quick avocado toast lunch", "Make a grain bowl", "Easy turkey wrap"],
            "evening": ["Cozy pasta carbonara tonight", "Quick weeknight stir fry", "Make a hearty soup", "Easy sheet pan dinner"],
        }
        return {"suggestions": fallbacks.get(time_of_day, fallbacks["evening"])}


def create_chat_sessions_router(broadcast_func):
    """Create chat sessions router with injected broadcast function"""
    global broadcast_event
    broadcast_event = broadcast_func
    return router
