"""
Redis client for pub/sub messaging between services.

This module provides a shared Redis client for:
- MCP service: Publishing tool outputs to UI
- API service: Subscribing to tool outputs and forwarding to WebSocket
"""
import os
import json
import asyncio
from typing import Optional, AsyncIterator
import redis.asyncio as redis
from redis.asyncio.client import PubSub


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
                    print(f"🔄 Connecting to Redis at {self.redis_url} (attempt {attempt + 1}/3)")
                    self._client = await redis.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                    await self._client.ping()
                    print("✅ Redis connection established")
                    return
                except Exception as e:
                    print(f"❌ Redis connection failed (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        print(f"⏳ Waiting {wait_time}s before retry...")
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
        print(f"📤 Published to Redis channel '{channel}': {message.get('content', {}).get('type', 'unknown')}")

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
            print(f"📥 Subscribed to Redis channel '{channel}'")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        print(f"📬 Received from Redis channel '{channel}': {data.get('content', {}).get('type', 'unknown')}")
                        yield data
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to decode Redis message: {e}")
                        continue
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            print(f"📭 Unsubscribed from Redis channel '{channel}'")

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
            print("🔌 Redis connection closed")

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


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get or create the global Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
