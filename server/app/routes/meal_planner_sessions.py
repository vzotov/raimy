from fastapi import APIRouter, HTTPException, Depends, Request
import logging

from ..services import database_service
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
        initial_message = request.initial_message if request else None
        session = await database_service.create_meal_planner_session(
            current_user["email"],
            initial_message
        )

        # Broadcast session created event via SSE
        if broadcast_event:
            await broadcast_event("session_created", {
                "id": session["id"],
                "session_name": session["session_name"],
                "room_name": session["room_name"]
            })

        return {
            "message": "Session created successfully",
            "session": session
        }
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("")
async def list_sessions(current_user: dict = Depends(get_current_user_with_storage)):
    """Get all meal planner sessions for the current user"""
    try:
        sessions = await database_service.get_user_meal_planner_sessions(current_user["email"])
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

        # Broadcast name update via SSE
        if broadcast_event:
            await broadcast_event("session_name_updated", {
                "id": session_id,
                "session_name": request.session_name
            })

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
