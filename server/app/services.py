from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc
from pydantic import BaseModel

from .database import AsyncSessionLocal
from .models import User, Recipe, RecipeStep, Session, MealPlannerSession, MealPlannerMessage
import uuid

logger = logging.getLogger(__name__)

# Pydantic models for API compatibility with existing Firebase service
class RecipeStepModel(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None
    ingredients: Optional[List[str]] = None

class RecipeModel(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    ingredients: List[str]
    steps: List[RecipeStepModel]
    total_time_minutes: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None
    meal_planner_session_id: Optional[str] = None

class DatabaseService:
    def __init__(self):
        pass

    async def save_recipe(self, recipe: RecipeModel) -> str:
        """Save a recipe to PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                # Create Recipe object
                db_recipe = Recipe(
                    name=recipe.name,
                    description=recipe.description,
                    ingredients=recipe.ingredients,
                    total_time_minutes=recipe.total_time_minutes,
                    difficulty=recipe.difficulty,
                    servings=recipe.servings,
                    tags=recipe.tags or [],
                    user_id=recipe.user_id,
                    meal_planner_session_id=recipe.meal_planner_session_id
                )

                db.add(db_recipe)
                await db.flush()  # Get the recipe ID

                # Create RecipeStep objects
                for step_data in recipe.steps:
                    db_step = RecipeStep(
                        recipe_id=db_recipe.id,
                        step_number=step_data.step_number,
                        instruction=step_data.instruction,
                        duration_minutes=step_data.duration_minutes,
                        ingredients=step_data.ingredients or []
                    )
                    db.add(db_step)

                await db.commit()
                return str(db_recipe.id)

            except Exception as e:
                await db.rollback()
                raise Exception(f"Failed to save recipe: {str(e)}")

    async def get_recipes(self) -> List[Dict[str, Any]]:
        """Get all recipes from PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                # Query all recipes with their steps
                result = await db.execute(
                    select(Recipe)
                    .options(selectinload(Recipe.steps))
                    .order_by(desc(Recipe.created_at))
                )
                recipes = result.scalars().all()

                # Convert to dict format compatible with existing API
                recipe_list = []
                for recipe in recipes:
                    recipe_dict = {
                        "id": str(recipe.id),
                        "name": recipe.name,
                        "description": recipe.description,
                        "ingredients": recipe.ingredients,
                        "total_time_minutes": recipe.total_time_minutes,
                        "difficulty": recipe.difficulty,
                        "servings": recipe.servings,
                        "tags": recipe.tags,
                        "user_id": recipe.user_id,
                        "created_at": recipe.created_at,
                        "updated_at": recipe.updated_at,
                        "steps": [
                            {
                                "step_number": step.step_number,
                                "instruction": step.instruction,
                                "duration_minutes": step.duration_minutes,
                                "ingredients": step.ingredients
                            }
                            for step in sorted(recipe.steps, key=lambda x: x.step_number)
                        ]
                    }
                    recipe_list.append(recipe_dict)

                return recipe_list

            except Exception as e:
                print(f"Error getting recipes: {e}")
                return []

    async def get_recipes_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recipes for a specific user from PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                # Query recipes by user_id with their steps
                result = await db.execute(
                    select(Recipe)
                    .options(selectinload(Recipe.steps))
                    .where(Recipe.user_id == user_id)
                    .order_by(desc(Recipe.created_at))
                )
                recipes = result.scalars().all()

                # Convert to dict format compatible with existing API
                recipe_list = []
                for recipe in recipes:
                    recipe_dict = {
                        "id": str(recipe.id),
                        "name": recipe.name,
                        "description": recipe.description,
                        "ingredients": recipe.ingredients,
                        "total_time_minutes": recipe.total_time_minutes,
                        "difficulty": recipe.difficulty,
                        "servings": recipe.servings,
                        "tags": recipe.tags,
                        "user_id": recipe.user_id,
                        "created_at": recipe.created_at,
                        "updated_at": recipe.updated_at,
                        "steps": [
                            {
                                "step_number": step.step_number,
                                "instruction": step.instruction,
                                "duration_minutes": step.duration_minutes,
                                "ingredients": step.ingredients
                            }
                            for step in sorted(recipe.steps, key=lambda x: x.step_number)
                        ]
                    }
                    recipe_list.append(recipe_dict)

                return recipe_list

            except Exception as e:
                print(f"Error getting recipes for user {user_id}: {e}")
                return []

    async def save_user(self, user_data: Dict[str, Any]) -> bool:
        """Save or update user data in PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                # Check if user exists
                result = await db.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    # Update existing user
                    existing_user.name = user_data.get("name", existing_user.name)
                    existing_user.picture = user_data.get("picture", existing_user.picture)
                    existing_user.locale = user_data.get("locale", existing_user.locale)
                    existing_user.last_login = datetime.utcnow()
                    existing_user.user_metadata = user_data.get("metadata", existing_user.user_metadata)
                else:
                    # Create new user
                    new_user = User(
                        email=user_data["email"],
                        name=user_data.get("name"),
                        picture=user_data.get("picture"),
                        locale=user_data.get("locale"),
                        last_login=datetime.utcnow(),
                        user_metadata=user_data.get("metadata", {})
                    )
                    db.add(new_user)

                await db.commit()
                return True

            except Exception as e:
                await db.rollback()
                print(f"Error saving user: {e}")
                return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        async with AsyncSessionLocal() as db:
            try:
                # Delete expired sessions
                now = datetime.utcnow()
                result = await db.execute(
                    select(Session).where(Session.expires_at < now)
                )
                expired_sessions = result.scalars().all()

                for session in expired_sessions:
                    await db.delete(session)

                await db.commit()
                return len(expired_sessions)

            except Exception as e:
                await db.rollback()
                print(f"Error cleaning up sessions: {e}")
                return 0

    # Meal Planner Session Methods

    async def create_meal_planner_session(
        self,
        user_id: str,
        initial_message: str = None,
        session_type: str = "meal-planner"
    ) -> Dict[str, Any]:
        """Create a new meal planner session with optional initial message"""
        async with AsyncSessionLocal() as db:
            try:
                session_id = uuid.uuid4()
                room_name = f"{session_type}-{session_id}"  # Include session type in room name

                # Create session
                new_session = MealPlannerSession(
                    id=session_id,
                    user_id=user_id,
                    session_name="Untitled Session",
                    session_type=session_type,
                    room_name=room_name
                )
                db.add(new_session)
                await db.flush()  # Flush to get the session ID for FK reference

                # Create initial message if provided
                message_data = []
                if initial_message:
                    initial_msg = MealPlannerMessage(
                        session_id=session_id,
                        role="user",
                        content=initial_message
                    )
                    db.add(initial_msg)
                    await db.flush()  # Flush to get created_at timestamp

                    message_data.append({
                        "role": initial_msg.role,
                        "content": initial_msg.content,
                        "timestamp": initial_msg.created_at.isoformat()
                    })

                await db.commit()

                return {
                    "id": str(session_id),
                    "user_id": user_id,
                    "session_name": "Untitled Session",
                    "session_type": session_type,
                    "room_name": room_name,
                    "messages": message_data,
                    "created_at": new_session.created_at.isoformat(),
                    "updated_at": new_session.updated_at.isoformat()
                }

            except Exception as e:
                await db.rollback()
                raise Exception(f"Failed to create meal planner session: {str(e)}")

    async def get_user_meal_planner_sessions(self, user_id: str, session_type: str = None) -> List[Dict[str, Any]]:
        """Get all meal planner sessions for a user, optionally filtered by session_type"""
        async with AsyncSessionLocal() as db:
            try:
                query = (
                    select(MealPlannerSession)
                    .options(selectinload(MealPlannerSession.message_records))
                    .where(MealPlannerSession.user_id == user_id)
                )

                # Filter by session_type if provided
                if session_type:
                    query = query.where(MealPlannerSession.session_type == session_type)

                query = query.order_by(desc(MealPlannerSession.updated_at))

                result = await db.execute(query)
                sessions = result.scalars().all()

                return [
                    {
                        "id": str(session.id),
                        "user_id": session.user_id,
                        "session_name": session.session_name,
                        "session_type": session.session_type,
                        "room_name": session.room_name,
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat()
                    }
                    for session in sessions
                ]

            except Exception as e:
                print(f"Error getting meal planner sessions for user {user_id}: {e}")
                return []

    async def get_meal_planner_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific meal planner session with full message history"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession)
                    .options(selectinload(MealPlannerSession.message_records))
                    .where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return None

                # Convert message records to API format with proper ISO timestamp
                messages = [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat()
                    }
                    for msg in session.message_records
                ]

                return {
                    "id": str(session.id),
                    "user_id": session.user_id,
                    "session_name": session.session_name,
                    "session_type": session.session_type,
                    "room_name": session.room_name,
                    "ingredients": session.ingredients or [],
                    "recipe": session.recipe or None,
                    "recipe_id": str(session.recipe_id) if session.recipe_id else None,
                    "messages": messages,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                }

            except Exception as e:
                print(f"Error getting meal planner session {session_id}: {e}")
                return None

    async def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: Union[str, Dict[str, Any]]  # Accept both strings and structured objects
    ) -> bool:
        """Add a message to a meal planner session

        Args:
            session_id: Session UUID
            role: Message role ('user' or 'assistant')
            content: Message content - can be plain string or structured MessageContent object
        """
        async with AsyncSessionLocal() as db:
            try:
                # Create new message
                new_message = MealPlannerMessage(
                    session_id=session_id,
                    role=role,
                    content=content
                )
                db.add(new_message)

                # Update session's updated_at timestamp
                result = await db.execute(
                    select(MealPlannerSession).where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if session:
                    session.updated_at = datetime.utcnow()

                await db.commit()
                return True

            except Exception as e:
                await db.rollback()
                print(f"Error adding message to session {session_id}: {e}")
                return False

    async def update_session_name(self, session_id: str, session_name: str) -> bool:
        """Update the name of a meal planner session"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession).where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return False

                session.session_name = session_name
                session.updated_at = datetime.utcnow()

                await db.commit()
                return True

            except Exception as e:
                await db.rollback()
                print(f"Error updating session name for {session_id}: {e}")
                return False

    async def delete_meal_planner_session(self, session_id: str) -> bool:
        """Delete a meal planner session"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession).where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return False

                await db.delete(session)
                await db.commit()
                return True

            except Exception as e:
                await db.rollback()
                print(f"Error deleting session {session_id}: {e}")
                return False

    async def save_or_update_ingredients(
        self,
        session_id: str,
        ingredients: List[Dict[str, Any]],
        action: str  # "set" or "update"
    ) -> bool:
        """Save or update ingredients directly on session."""
        logger.info(f"🥘 save_or_update_ingredients: session={session_id}, action={action}, items={ingredients}")

        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession)
                    .where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()
                logger.info(f"🔍 Fetched session from DB with items={session.ingredients}")

                if not session:
                    logger.error(f"❌ Session not found: {session_id}")
                    return False

                if action == "set":
                    # Replace entire ingredient list
                    logger.info(f"📝 Setting {len(ingredients)} ingredients")
                    session.ingredients = ingredients

                elif action == "update":
                    # Merge updates with existing by name
                    existing = session.ingredients or []
                    logger.info(f"🔄 Updating: {len(existing)} existing + {len(ingredients)} updates")
                    item_map = {item["name"]: item for item in existing}

                    for update in ingredients:
                        name = update.get("name")
                        if name in item_map:
                            logger.debug(f"  Updating existing: {name}")
                            item_map[name].update(update)
                        else:
                            logger.debug(f"  Adding new: {name}")
                            item_map[name] = update

                    session.ingredients = list(item_map.values())
                    flag_modified(session, "ingredients")
                    logger.info(f"✅ Final ingredient count: {len(session.ingredients)}")

                session.updated_at = datetime.utcnow()
                await db.commit()
                logger.info(f"💾 Committed to DB successfully. Saved session state: id={session.id}, ingredients={session.ingredients}, updated_at={session.updated_at.isoformat()}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"❌ Error saving/updating ingredients for session {session_id}: {e}", exc_info=True)
                return False

    async def save_or_update_recipe(
        self,
        session_id: str,
        action: str,  # "set_metadata", "set_ingredients", "set_steps"
        **update_data
    ) -> bool:
        """Save or update recipe data on session with action-based merging."""
        logger.info(f"📝 save_or_update_recipe: session={session_id}, action={action}")

        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession)
                    .where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    logger.error(f"❌ Session not found: {session_id}")
                    return False

                # Get existing recipe or initialize empty
                recipe = session.recipe or {}

                # Merge based on action type
                if action == "set_metadata":
                    # Update metadata fields
                    if "name" in update_data:
                        recipe["name"] = update_data["name"]
                    if "description" in update_data:
                        recipe["description"] = update_data["description"]
                    if "difficulty" in update_data:
                        recipe["difficulty"] = update_data["difficulty"]
                    if "total_time" in update_data:
                        recipe["total_time"] = update_data["total_time"]
                    if "servings" in update_data:
                        recipe["servings"] = update_data["servings"]
                    if "tags" in update_data:
                        recipe["tags"] = update_data["tags"]

                elif action == "set_ingredients":
                    # Replace entire ingredients array
                    recipe["ingredients"] = update_data.get("ingredients", [])

                elif action == "set_steps":
                    # Replace entire steps array
                    recipe["steps"] = update_data.get("steps", [])

                session.recipe = recipe
                flag_modified(session, "recipe")
                session.updated_at = datetime.utcnow()

                await db.commit()
                logger.info(f"💾 Recipe updated: action={action}, recipe={recipe}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"❌ Error updating recipe: {e}", exc_info=True)
                return False

    async def update_session_recipe_id(
        self,
        session_id: str,
        recipe_id: str
    ) -> bool:
        """Update session's recipe_id FK when recipe is saved."""
        logger.info(f"🔗 update_session_recipe_id: session={session_id}, recipe_id={recipe_id}")

        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession)
                    .where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    logger.error(f"❌ Session not found: {session_id}")
                    return False

                session.recipe_id = recipe_id
                session.updated_at = datetime.utcnow()
                await db.commit()

                logger.info(f"✅ Session recipe_id updated: {recipe_id}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"❌ Error updating recipe_id: {e}", exc_info=True)
                return False

# Global instance
database_service = DatabaseService()