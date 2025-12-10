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
        initial_message = request.initial_message if request else None
        session_type = request.session_type if request else "meal-planner"
        session = await database_service.create_meal_planner_session(
            current_user["email"],
            initial_message,
            session_type
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
    logger.info(f"🔍 API: Current user data: {current_user}")

    try:
        # Get session and verify ownership
        logger.info(f"🔍 API: Fetching session data for session_id={session_id}")
        session_data = await database_service.get_meal_planner_session(session_id)

        if not session_data:
            logger.error(f"❌ API: Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"✅ API: Session found, user_id={session_data['user_id']}, recipe_id={session_data.get('recipe_id')}")

        # Allow service account to access any session, but regular users can only access their own
        # Service account is identified by the special email in the JWT token
        is_service_account = current_user.get("email") == "service@raimy.internal"
        logger.info(f"🔍 API: is_service_account={is_service_account}")

        if not is_service_account and session_data["user_id"] != current_user["email"]:
            logger.error(f"❌ API: User {current_user['email']} not authorized for session owned by {session_data['user_id']}")
            raise HTTPException(status_code=403, detail="Not authorized")

        if is_service_account:
            logger.info(f"🔓 API: Service account access granted for session owned by {session_data['user_id']}")

        # Get recipe from session
        recipe_json = session_data.get("recipe")

        if not recipe_json:
            raise HTTPException(
                status_code=400,
                detail="No recipe found in session. Build a recipe first using the chat."
            )

        # Validate required fields
        required = ["name", "ingredients", "steps"]
        missing = [f for f in required if not recipe_json.get(f)]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Recipe is incomplete. Missing: {', '.join(missing)}"
            )

        # Helper to parse time string
        def parse_time_string(time_str: str) -> int:
            """Parse '30 minutes' or '1 hour' to minutes"""
            if not time_str:
                return None
            lower = time_str.lower()
            import re
            match = re.match(r'(\d+(?:\.\d+)?)', lower)
            if not match:
                return None
            num = float(match.group(1))
            if 'hour' in lower:
                return int(num * 60)
            return int(num)

        # Convert ingredients to RecipeIngredientModel objects
        ingredients = [
            RecipeIngredientModel(**ing_data)
            for ing_data in recipe_json.get("ingredients", [])
        ]

        # Convert steps to RecipeStepModel objects
        steps = [
            RecipeStepModel(
                instruction=step_data["instruction"],
                duration=step_data.get("duration")
            )
            for step_data in recipe_json["steps"]
        ]

        # Parse total_time if it's a string
        total_time_minutes = recipe_json.get("total_time_minutes")
        if not total_time_minutes and recipe_json.get("total_time"):
            total_time_minutes = parse_time_string(recipe_json["total_time"])

        # Create RecipeModel
        # Use the session owner's email as user_id (not the service account)
        owner_email = session_data["user_id"]
        recipe_model = RecipeModel(
            name=recipe_json["name"],
            description=recipe_json.get("description", ""),
            ingredients=ingredients,
            steps=steps,
            total_time_minutes=total_time_minutes,
            difficulty=recipe_json.get("difficulty", "medium"),
            servings=recipe_json.get("servings", 4),
            tags=recipe_json.get("tags", []),
            user_id=owner_email,
            meal_planner_session_id=session_id
        )

        # Check if recipe already saved (update vs create)
        existing_recipe_id = session_data.get("recipe_id")

        logger.info(f"🔍 API: Checking existing recipe_id={existing_recipe_id}")
        logger.info(f"📊 API: Session data keys: {list(session_data.keys())}")
        logger.info(f"📊 API: Recipe JSON exists: {session_data.get('recipe') is not None}")

        if existing_recipe_id:
            # Update existing recipe
            logger.info(f"🔄 API: UPDATING existing recipe with ID: {existing_recipe_id}")
            recipe_model.id = existing_recipe_id
            recipe_id = await database_service.save_recipe(recipe_model)
            logger.info(f"✅ API: Updated recipe {recipe_id} from session {session_id}")
        else:
            # Save new recipe
            logger.info(f"➕ API: CREATING new recipe (no existing recipe_id)")
            recipe_id = await database_service.save_recipe(recipe_model)
            logger.info(f"✅ API: Created new recipe with ID: {recipe_id}")

            # Update session.recipe_id
            logger.info(f"🔗 API: Linking recipe {recipe_id} to session {session_id}")
            await database_service.update_session_recipe_id(session_id, recipe_id)
            logger.info(f"✅ API: Session recipe_id updated successfully")

        return {
            "message": "Recipe saved successfully",
            "recipe_id": recipe_id,
            "recipe": recipe_model.dict()
        }

    except HTTPException:
        raise
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
