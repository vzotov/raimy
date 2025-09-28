from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc
from pydantic import BaseModel

from .database import AsyncSessionLocal
from .models import User, Recipe, RecipeStep, Session

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

# Global instance
database_service = DatabaseService()