"""
Memory Agent

Extracts user preferences from conversations and maintains a memory document.
Runs as a fire-and-forget task after other agents complete.
"""

import os
import logging
from typing import Dict, List, Optional, Any

from langchain_openai import ChatOpenAI

from .prompt import MEMORY_EXTRACTION_PROMPT, EMPTY_MEMORY_TEMPLATE
from app.services import database_service

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Shared agent for extracting user preferences from conversations.
    Called at the end of other agents' sessions.
    """

    MODEL = "gpt-4o-mini"

    def __init__(self):
        self.llm = ChatOpenAI(
            model=self.MODEL,
            temperature=0.3,  # Lower temperature for consistent extraction
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        logger.info(f"🧠 MemoryAgent initialized with model: {self.MODEL}")

    def _format_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format message history for the LLM prompt."""
        if not messages:
            return "(No messages)"

        formatted = []
        for msg in messages[-10:]:  # Last 10 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Handle structured content
            if isinstance(content, dict):
                content_type = content.get("type", "")
                if content_type == "text":
                    content = content.get("content", "")
                elif content_type == "selector":
                    content = content.get("message", "")
                elif content_type == "kitchen-step":
                    content = content.get("message", "")
                else:
                    content = str(content)

            role_label = "User" if role == "user" else "Assistant"
            formatted.append(f"{role_label}: {content}")

        return "\n".join(formatted)

    async def extract_and_save(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
        current_memory: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extract preferences from conversation and save to database.

        Args:
            user_id: User email (primary key)
            messages: Conversation messages from the session
            current_memory: Existing memory document or None

        Returns:
            Updated memory document or None if no changes
        """
        # Skip if no user messages
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            logger.debug(f"🧠 No user messages to extract from for {user_id}")
            return None

        # Format conversation for LLM
        conversation = self._format_conversation(messages)

        # Use empty template if no existing memory
        memory_to_use = current_memory or EMPTY_MEMORY_TEMPLATE

        # Call LLM to extract/update memory
        prompt = MEMORY_EXTRACTION_PROMPT.format(
            current_memory=memory_to_use,
            conversation=conversation,
        )

        try:
            response = await self.llm.ainvoke(prompt)
            updated_memory = response.content.strip()

            # Clean up markdown code block if LLM wrapped it
            if updated_memory.startswith("```markdown"):
                updated_memory = updated_memory[11:]
            if updated_memory.startswith("```"):
                updated_memory = updated_memory[3:]
            if updated_memory.endswith("```"):
                updated_memory = updated_memory[:-3]
            updated_memory = updated_memory.strip()

            # Check if memory actually changed
            if updated_memory and updated_memory != current_memory:
                # Save to database
                success = await database_service.save_user_memory(user_id, updated_memory)
                if success:
                    logger.info(f"🧠 Memory updated for user {user_id}")
                    return updated_memory
                else:
                    logger.error(f"🧠 Failed to save memory for user {user_id}")
                    return None

            logger.debug(f"🧠 No memory changes for user {user_id}")
            return None

        except Exception as e:
            logger.error(f"🧠 Memory extraction failed for {user_id}: {e}", exc_info=True)
            return None


# Global singleton instance
memory_agent = MemoryAgent()
