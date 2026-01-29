"""
Redis client for pub/sub messaging between services.

This module provides a shared Redis client for:
- Agent service: Publishing messages to UI
- API service: Subscribing to messages and forwarding to WebSocket
"""
import os
import json
import asyncio
import logging
from typing import Optional, AsyncIterator
import redis.asyncio as redis
from redis.asyncio.client import PubSub

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with pub/sub support"""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self._connection_lock = asyncio.Lock()

    async def _ensure_connected(self):
        """Ensure Redis connection is established with retry logic"""
        if self._client is not None:
            try:
                await self._client.ping()
                return
            except Exception:
                self._client = None

        async with self._connection_lock:
            if self._client is not None:
                return

            for attempt in range(3):
                try:
                    logger.warning(f"🔄 Connecting to Redis at {self.redis_url} (attempt {attempt + 1}/3)")
                    self._client = await redis.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                    await self._client.ping()
                    logger.warning("✅ Redis connection established")
                    return
                except Exception as e:
                    logger.error(f"❌ Redis connection failed (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        logger.warning(f"⏳ Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)

            raise ConnectionError("Failed to connect to Redis after 3 attempts")

    async def publish(self, channel: str, message: dict):
        """
        Publish a message to a Redis channel.

        Args:
            channel: Redis channel name (e.g., "session:abc-123")
            message: Message dictionary to publish (will be JSON-encoded)
        """
        await self._ensure_connected()
        message_json = json.dumps(message)
        await self._client.publish(channel, message_json)

    async def subscribe(self, channel: str) -> AsyncIterator[dict]:
        """
        Subscribe to a Redis channel and yield messages.

        Args:
            channel: Redis channel name (e.g., "session:abc-123")

        Yields:
            Message dictionaries received from the channel
        """
        await self._ensure_connected()
        pubsub: PubSub = self._client.pubsub()

        try:
            await pubsub.subscribe(channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Failed to decode Redis message: {e}")
                        continue
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    async def send_system_message(self, session_id: str, message_type: str, message: str):
        """
        Send a system message to a session

        Args:
            session_id: Session ID
            message_type: Type of system message (e.g., "thinking", "error", "connected")
            message: Message content
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "system",
                "content": {
                    "type": message_type,
                    "message": message
                }
            }
        )

    async def send_agent_text_message(
        self,
        session_id: str,
        content: str,
        message_id: str
    ):
        """
        Send an agent text message to a session

        Args:
            session_id: Session ID
            content: Text content
            message_id: Unique message ID
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "text",
                    "content": content
                },
                "message_id": message_id
            }
        )

    async def send_recipe_save_request(self, session_id: str):
        """
        Send a recipe save request message to a session.
        This triggers the API service to save the session's recipe to the Recipe table.

        Args:
            session_id: Session ID
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "save_recipe"
                }
            }
        )

    async def send_ingredients_message(self, session_id: str, items: list, action: str = "set"):
        """
        Send ingredients message to update session ingredients.

        Args:
            session_id: Session ID
            items: List of ingredient dictionaries
            action: "set" or "update"
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "ingredients",
                    "items": items,
                    "action": action
                }
            }
        )

    async def send_timer_message(self, session_id: str, duration: int, label: str):
        """
        Send timer message to set a cooking timer.

        Args:
            session_id: Session ID
            duration: Duration in seconds
            label: Timer label
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "timer",
                    "duration": duration,
                    "label": label
                }
            }
        )

    async def send_session_name_message(self, session_id: str, name: str):
        """
        Send session name message to update session name.

        Args:
            session_id: Session ID
            name: Session name
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "session_name",
                    "name": name
                }
            }
        )

    async def send_recipe_metadata_message(
        self,
        session_id: str,
        name: str = None,
        description: str = None,
        difficulty: str = None,
        total_time_minutes: int = None,
        servings: int = None,
        tags: list = None
    ):
        """
        Send recipe metadata message to update session.recipe.

        Args:
            session_id: Session ID
            name: Recipe name
            description: Recipe description
            difficulty: Difficulty level
            total_time_minutes: Total time in minutes
            servings: Number of servings
            tags: List of tags
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_metadata",
                    "name": name,
                    "description": description,
                    "difficulty": difficulty,
                    "total_time_minutes": total_time_minutes,
                    "servings": servings,
                    "tags": tags
                }
            }
        )

    async def send_recipe_ingredients_message(self, session_id: str, ingredients: list):
        """
        Send recipe ingredients message to update session.recipe.

        Args:
            session_id: Session ID
            ingredients: List of ingredient dictionaries
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_ingredients",
                    "ingredients": ingredients
                }
            }
        )

    async def send_recipe_steps_message(self, session_id: str, steps: list):
        """
        Send recipe steps message to update session.recipe.

        Args:
            session_id: Session ID
            steps: List of step dictionaries
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_steps",
                    "steps": steps
                }
            }
        )

    async def send_recipe_nutrition_message(self, session_id: str, nutrition: dict):
        """
        Send recipe nutrition message to update session.recipe.

        Args:
            session_id: Session ID
            nutrition: Nutrition data dict (e.g., {"calories": 850, "carbs": 65, "fats": 32, "proteins": 45})
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "recipe_update",
                    "action": "set_nutrition",
                    "nutrition": nutrition
                }
            }
        )

    async def send_step_update_message(
        self,
        session_id: str,
        step_index: int,
        step_instruction: str,
        total_steps: int
    ):
        """
        Send step update message for kitchen cooking guidance.

        Args:
            session_id: Session ID
            step_index: Current step index (0-based)
            step_instruction: Step instruction text
            total_steps: Total number of steps in recipe
        """
        await self.publish(
            f"session:{session_id}",
            {
                "type": "agent_message",
                "content": {
                    "type": "step_update",
                    "step_index": step_index,
                    "step_instruction": step_instruction,
                    "total_steps": total_steps
                }
            }
        )

    def is_agent_message(self, message: dict, content_type: str = None) -> bool:
        """
        Check if a message is an agent message, optionally with specific content type

        Args:
            message: Redis message dictionary
            content_type: Optional content type to check (e.g., 'ingredients', 'recipe_name', 'text')

        Returns:
            True if message matches criteria, False otherwise

        Examples:
            is_agent_message(msg)  # Check if any agent message
            is_agent_message(msg, 'ingredients')  # Check if ingredients message
            is_agent_message(msg, 'recipe_name')  # Check if recipe_name message
        """
        if message.get("type") != "agent_message":
            return False

        if not isinstance(message.get("content"), dict):
            return False

        if content_type is None:
            return True

        return message.get("content", {}).get("type") == content_type


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get or create the global Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
