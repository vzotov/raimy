from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc, delete
from pydantic import BaseModel

from .database import AsyncSessionLocal
from .models import User, Recipe, Session, ChatSession, ChatMessage
import uuid

logger = logging.getLogger(__name__)

# Pydantic models for API - match JSON structure exactly
class RecipeIngredientModel(BaseModel):
    """Ingredient: {"name": "eggs", "amount": "4", "unit": null, "notes": "optional"}"""
    name: str
    amount: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None

class RecipeStepModel(BaseModel):
    """Step: {"instruction": "Boil water", "duration": 10}"""
    instruction: str
    duration: Optional[int] = None  # Duration in minutes

class RecipeModel(BaseModel):
    """Recipe model matching database JSON structure"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    ingredients: List[RecipeIngredientModel]
    steps: List[RecipeStepModel]
    total_time_minutes: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None
    chat_session_id: Optional[str] = None

class DatabaseService:
    def __init__(self):
        pass

    async def save_recipe(self, recipe: RecipeModel) -> str:
        """Save or update a recipe in PostgreSQL (create if no ID, update if ID exists)"""
        logger.info(f"🟢 DB SERVICE: save_recipe called with recipe.id={recipe.id}, name='{recipe.name}'")

        async with AsyncSessionLocal() as db:
            try:
                # Convert Pydantic models to JSON dicts
                ingredients_json = [ing.model_dump() for ing in recipe.ingredients]
                steps_json = [step.model_dump() for step in recipe.steps]

                if recipe.id:
                    # Update existing recipe
                    logger.info(f"🔄 DB: Updating existing recipe with ID: {recipe.id}")
                    result = await db.execute(
                        select(Recipe).where(Recipe.id == recipe.id)
                    )
                    db_recipe = result.scalar_one_or_none()

                    if not db_recipe:
                        logger.error(f"❌ DB: Recipe {recipe.id} not found for update")
                        raise Exception(f"Recipe {recipe.id} not found for update")

                    logger.info(f"✅ DB: Found existing recipe, updating all fields")

                    # Update all fields including JSON columns
                    db_recipe.name = recipe.name
                    db_recipe.description = recipe.description
                    db_recipe.ingredients = ingredients_json
                    db_recipe.steps = steps_json
                    db_recipe.total_time_minutes = recipe.total_time_minutes
                    db_recipe.difficulty = recipe.difficulty
                    db_recipe.servings = recipe.servings
                    db_recipe.tags = recipe.tags or []

                    # Mark JSON fields as modified
                    flag_modified(db_recipe, "ingredients")
                    flag_modified(db_recipe, "steps")

                    await db.commit()
                    logger.info(f"✅ DB: Recipe {db_recipe.id} updated successfully")
                    return str(db_recipe.id)

                else:
                    # Create new recipe
                    logger.info(f"➕ DB: Creating new recipe '{recipe.name}'")
                    db_recipe = Recipe(
                        name=recipe.name,
                        description=recipe.description,
                        ingredients=ingredients_json,
                        steps=steps_json,
                        total_time_minutes=recipe.total_time_minutes,
                        difficulty=recipe.difficulty,
                        servings=recipe.servings,
                        tags=recipe.tags or [],
                        user_id=recipe.user_id,
                        chat_session_id=recipe.chat_session_id
                    )

                    db.add(db_recipe)
                    await db.commit()
                    await db.refresh(db_recipe)  # Get the recipe ID and timestamps
                    logger.info(f"✅ DB: Recipe {db_recipe.id} saved successfully with {len(steps_json)} steps")
                    return str(db_recipe.id)

            except Exception as e:
                await db.rollback()
                logger.error(f"❌ DB: Failed to save recipe: {str(e)}", exc_info=True)
                raise Exception(f"Failed to save recipe: {str(e)}")

    async def get_recipes(self) -> List[Dict[str, Any]]:
        """Get all recipes from PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                # Query all recipes (ingredients and steps are JSON columns)
                result = await db.execute(
                    select(Recipe)
                    .order_by(desc(Recipe.created_at))
                )
                recipes = result.scalars().all()

                # Convert to dict format
                recipe_list = []
                for recipe in recipes:
                    recipe_dict = {
                        "id": str(recipe.id),
                        "name": recipe.name,
                        "description": recipe.description,
                        "ingredients": recipe.ingredients,
                        "steps": recipe.steps,
                        "total_time_minutes": recipe.total_time_minutes,
                        "difficulty": recipe.difficulty,
                        "servings": recipe.servings,
                        "tags": recipe.tags,
                        "user_id": recipe.user_id,
                        "created_at": recipe.created_at,
                        "updated_at": recipe.updated_at,
                    }
                    recipe_list.append(recipe_dict)

                return recipe_list

            except Exception as e:
                logger.error(f"Error getting recipes: {e}", exc_info=True)
                return []

    async def get_recipes_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recipes for a specific user from PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                # Query recipes by user_id (ingredients and steps are JSON columns)
                result = await db.execute(
                    select(Recipe)
                    .where(Recipe.user_id == user_id)
                    .order_by(desc(Recipe.created_at))
                )
                recipes = result.scalars().all()

                # Convert to dict format
                recipe_list = []
                for recipe in recipes:
                    recipe_dict = {
                        "id": str(recipe.id),
                        "name": recipe.name,
                        "description": recipe.description,
                        "ingredients": recipe.ingredients,
                        "steps": recipe.steps,
                        "total_time_minutes": recipe.total_time_minutes,
                        "difficulty": recipe.difficulty,
                        "servings": recipe.servings,
                        "tags": recipe.tags,
                        "user_id": recipe.user_id,
                        "created_at": recipe.created_at,
                        "updated_at": recipe.updated_at,
                    }
                    recipe_list.append(recipe_dict)

                return recipe_list

            except Exception as e:
                logger.error(f"Error getting recipes for user {user_id}: {e}", exc_info=True)
                return []

    async def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get a single recipe by ID from PostgreSQL"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(Recipe).where(Recipe.id == recipe_id)
                )
                recipe = result.scalar_one_or_none()

                if not recipe:
                    return None

                return {
                    "id": str(recipe.id),
                    "name": recipe.name,
                    "description": recipe.description,
                    "ingredients": recipe.ingredients,
                    "steps": recipe.steps,
                    "total_time_minutes": recipe.total_time_minutes,
                    "difficulty": recipe.difficulty,
                    "servings": recipe.servings,
                    "tags": recipe.tags,
                    "user_id": recipe.user_id,
                    "chat_session_id": str(recipe.chat_session_id) if recipe.chat_session_id else None,
                    "created_at": recipe.created_at,
                    "updated_at": recipe.updated_at,
                }
            except Exception as e:
                logger.error(f"Error getting recipe {recipe_id}: {e}", exc_info=True)
                return None

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

    # Chat Session Methods

    async def create_chat_session(
        self,
        user_id: str,
        session_type: str = "recipe-creator",
        recipe_id: str = None
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        async with AsyncSessionLocal() as db:
            try:
                session_id = uuid.uuid4()
                room_name = f"{session_type}-{session_id}"  # Include session type in room name

                # Pre-populate session data from recipe if recipe_id is provided
                session_name = "Untitled Session"
                ingredients = None

                if recipe_id:
                    recipe_data = await self.get_recipe_by_id(recipe_id)
                    if recipe_data:
                        session_name = recipe_data.get("name", "Untitled Session")
                        # Convert recipe ingredients to session ingredients format
                        recipe_ingredients = recipe_data.get("ingredients", [])
                        if recipe_ingredients:
                            ingredients = [
                                {
                                    "name": ing.get("name"),
                                    "amount": ing.get("amount", ""),
                                    "unit": ing.get("unit", ""),
                                    "highlighted": False,
                                    "used": False
                                }
                                for ing in recipe_ingredients
                            ]
                        logger.info(f"📋 Pre-populated session with recipe '{session_name}' and {len(ingredients) if ingredients else 0} ingredients")
                    else:
                        logger.warning(f"⚠️  Recipe {recipe_id} not found during session creation")

                # Create session
                new_session = ChatSession(
                    id=session_id,
                    user_id=user_id,
                    session_name=session_name,
                    session_type=session_type,
                    room_name=room_name,
                    recipe_id=recipe_id,
                    ingredients=ingredients
                )
                db.add(new_session)
                await db.commit()

                return {
                    "id": str(session_id),
                    "user_id": user_id,
                    "session_name": session_name,
                    "session_type": session_type,
                    "room_name": room_name,
                    "messages": [],
                    "created_at": new_session.created_at.isoformat(),
                    "updated_at": new_session.updated_at.isoformat()
                }

            except Exception as e:
                await db.rollback()
                raise Exception(f"Failed to create chat session: {str(e)}")

    async def get_user_chat_sessions(self, user_id: str, session_type: str = None) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user, optionally filtered by session_type"""
        async with AsyncSessionLocal() as db:
            try:
                query = (
                    select(ChatSession)
                    .options(selectinload(ChatSession.message_records))
                    .where(ChatSession.user_id == user_id)
                )

                # Filter by session_type if provided
                if session_type:
                    query = query.where(ChatSession.session_type == session_type)

                query = query.order_by(desc(ChatSession.updated_at))

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
                print(f"Error getting chat sessions for user {user_id}: {e}")
                return []

    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific chat session with full message history"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(ChatSession)
                    .options(selectinload(ChatSession.message_records))
                    .where(ChatSession.id == session_id)
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
                print(f"Error getting chat session {session_id}: {e}")
                return None

    async def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: Union[str, Dict[str, Any]]  # Accept both strings and structured objects
    ) -> bool:
        """Add a message to a chat session

        Args:
            session_id: Session UUID
            role: Message role ('user' or 'assistant')
            content: Message content - can be plain string or structured MessageContent object
        """
        async with AsyncSessionLocal() as db:
            try:
                # Create new message
                new_message = ChatMessage(
                    session_id=session_id,
                    role=role,
                    content=content
                )
                db.add(new_message)

                # Update session's updated_at timestamp
                result = await db.execute(
                    select(ChatSession).where(ChatSession.id == session_id)
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
        """Update the name of a chat session"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(ChatSession).where(ChatSession.id == session_id)
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

    async def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(ChatSession).where(ChatSession.id == session_id)
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
                    select(ChatSession)
                    .where(ChatSession.id == session_id)
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
        logger.info(f"📝 save_or_update_recipe: update_data={update_data}")

        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(ChatSession)
                    .where(ChatSession.id == session_id)
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
                    if "total_time_minutes" in update_data:
                        recipe["total_time_minutes"] = update_data["total_time_minutes"]
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
                    select(ChatSession)
                    .where(ChatSession.id == session_id)
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

    async def save_recipe_from_session_data(self, session_id: str) -> dict:
        """
        Save recipe from session.recipe JSON directly to Recipe table.

        Args:
            session_id: Session ID

        Returns:
            dict: {"recipe_id": str, "recipe": dict}
        """
        logger.info(f"💾 save_recipe_from_session_data: session={session_id}")

        # Get session data
        session_data = await self.get_chat_session(session_id)
        recipe_json = session_data["recipe"]
        owner_email = session_data["user_id"]
        existing_recipe_id = session_data.get("recipe_id")

        async with AsyncSessionLocal() as db:
            try:
                if existing_recipe_id:
                    # Update existing recipe
                    logger.info(f"🔄 Updating recipe {existing_recipe_id}")

                    result = await db.execute(
                        select(Recipe).where(Recipe.id == existing_recipe_id)
                    )
                    db_recipe = result.scalar_one()

                    db_recipe.name = recipe_json.get("name", db_recipe.name)
                    db_recipe.description = recipe_json.get("description", "")
                    db_recipe.ingredients = recipe_json.get("ingredients", [])
                    db_recipe.steps = recipe_json.get("steps", [])
                    db_recipe.total_time_minutes = recipe_json.get("total_time_minutes")
                    db_recipe.difficulty = recipe_json.get("difficulty", "medium")
                    db_recipe.servings = recipe_json.get("servings", 4)
                    db_recipe.tags = recipe_json.get("tags", [])

                    flag_modified(db_recipe, "ingredients")
                    flag_modified(db_recipe, "steps")

                    await db.commit()
                    recipe_id = str(db_recipe.id)
                else:
                    # Create new recipe
                    logger.info(f"➕ Creating new recipe")

                    db_recipe = Recipe(
                        name=recipe_json.get("name", "Untitled Recipe"),
                        description=recipe_json.get("description", ""),
                        ingredients=recipe_json.get("ingredients", []),
                        steps=recipe_json.get("steps", []),
                        total_time_minutes=recipe_json.get("total_time_minutes"),
                        difficulty=recipe_json.get("difficulty", "medium"),
                        servings=recipe_json.get("servings", 4),
                        tags=recipe_json.get("tags", []),
                        user_id=owner_email,
                        chat_session_id=session_id
                    )

                    db.add(db_recipe)
                    await db.commit()
                    await db.refresh(db_recipe)
                    recipe_id = str(db_recipe.id)

                    # Link recipe to session
                    await self.update_session_recipe_id(session_id, recipe_id)

                logger.info(f"✅ Recipe saved: {recipe_id}")

                return {
                    "recipe_id": recipe_id,
                    "recipe": {
                        "id": recipe_id,
                        "name": db_recipe.name,
                        "description": db_recipe.description,
                        "ingredients": db_recipe.ingredients,
                        "steps": db_recipe.steps,
                        "total_time_minutes": db_recipe.total_time_minutes,
                        "difficulty": db_recipe.difficulty,
                        "servings": db_recipe.servings,
                        "tags": db_recipe.tags,
                        "user_id": db_recipe.user_id
                    }
                }

            except Exception as e:
                await db.rollback()
                logger.error(f"❌ Error saving recipe: {e}", exc_info=True)
                raise

# Global instance
database_service = DatabaseService()