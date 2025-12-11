from fastapi import APIRouter, HTTPException, Depends, Request
import logging
from typing import List

from ..services import database_service, RecipeModel, RecipeStepModel, RecipeIngredientModel
from .models import UpdateSessionNameRequest, CreateSessionRequest
from core.auth_client import auth_client

logger = logging.getLogger(__name__)

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

router = APIRouter(prefix="/api/meal-planner-sessions", tags=["meal_planner_sessions"])


@router.post("")
async def create_session(
    request: CreateSessionRequest = None,
    current_user: dict = Depends(get_current_user_with_storage)
):
    """Create a new meal planner session"""
    try:
        session_type = request.session_type if request else "meal-planner"
        recipe_id = request.recipe_id if request else None
        session = await database_service.create_meal_planner_session(
            current_user["email"],
            session_type,
            recipe_id
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
    """Get all sessions for the current user, optionally filtered by session_type (meal-planner or kitchen)"""
    try:
        sessions = await database_service.get_user_meal_planner_sessions(
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
    """Get a specific meal planner session with full message history"""
    try:
        session = await database_service.get_meal_planner_session(session_id)

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
    """Update the name of a meal planner session"""
    try:
        # First verify session exists and user owns it
        session = await database_service.get_meal_planner_session(session_id)

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
        session_data = await database_service.get_meal_planner_session(session_id)

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


@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user_with_storage)):
    """Delete a meal planner session"""
    try:
        # First verify session exists and user owns it
        session = await database_service.get_meal_planner_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session["user_id"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete the session
        success = await database_service.delete_meal_planner_session(session_id)

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


def create_meal_planner_sessions_router(broadcast_func):
    """Create meal planner sessions router with injected broadcast function"""
    global broadcast_event
    broadcast_event = broadcast_func
    return router
