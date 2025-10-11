from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc
from pydantic import BaseModel

from .database import AsyncSessionLocal
from .models import User, Recipe, RecipeStep, Session, MealPlannerSession
import uuid

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
                    user_id=recipe.user_id
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

    async def create_meal_planner_session(self, user_id: str) -> Dict[str, Any]:
        """Create a new meal planner session"""
        async with AsyncSessionLocal() as db:
            try:
                session_id = uuid.uuid4()
                room_name = f"meal-planner-{session_id}"

                new_session = MealPlannerSession(
                    id=session_id,
                    user_id=user_id,
                    session_name="Untitled Session",
                    room_name=room_name,
                    messages=[]
                )

                db.add(new_session)
                await db.commit()

                return {
                    "id": str(session_id),
                    "user_id": user_id,
                    "session_name": "Untitled Session",
                    "room_name": room_name,
                    "messages": [],
                    "created_at": new_session.created_at,
                    "updated_at": new_session.updated_at
                }

            except Exception as e:
                await db.rollback()
                raise Exception(f"Failed to create meal planner session: {str(e)}")

    async def get_user_meal_planner_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all meal planner sessions for a user"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession)
                    .where(MealPlannerSession.user_id == user_id)
                    .order_by(desc(MealPlannerSession.updated_at))
                )
                sessions = result.scalars().all()

                return [
                    {
                        "id": str(session.id),
                        "user_id": session.user_id,
                        "session_name": session.session_name,
                        "room_name": session.room_name,
                        "message_count": len(session.messages) if session.messages else 0,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at
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
                    select(MealPlannerSession).where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return None

                return {
                    "id": str(session.id),
                    "user_id": session.user_id,
                    "session_name": session.session_name,
                    "room_name": session.room_name,
                    "messages": session.messages or [],
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                }

            except Exception as e:
                print(f"Error getting meal planner session {session_id}: {e}")
                return None

    async def append_session_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Append a new message to a session's message history"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MealPlannerSession).where(MealPlannerSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return False

                # Append message to messages array
                messages = session.messages or []
                messages.append(message)
                session.messages = messages
                session.updated_at = datetime.utcnow()

                await db.commit()
                return True

            except Exception as e:
                await db.rollback()
                print(f"Error appending message to session {session_id}: {e}")
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

# Global instance
database_service = DatabaseService()