"""
Memory Extraction Script

Extracts user memories from existing chat sessions by aggregating messages
and running them through the MemoryAgent.

Usage:
    python -m scripts.extract_memories              # All users
    python -m scripts.extract_memories --dry-run    # Preview without saving
    python -m scripts.extract_memories --user EMAIL # Single user only
    python -m scripts.extract_memories --force      # Re-extract even if memory exists
"""

import asyncio
import argparse
import logging
import sys
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import User, ChatSession, UserMemory
from app.services import database_service
from agents.memory.agent import memory_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def get_users_with_sessions(user_email: Optional[str] = None) -> List[User]:
    """
    Get users who have chat sessions.

    Args:
        user_email: If provided, filter to this specific user

    Returns:
        List of User objects with chat_sessions relationship loaded
    """
    async with AsyncSessionLocal() as db:
        # First get distinct user emails that have sessions
        # (avoids DISTINCT on JSON columns which PostgreSQL can't handle)
        email_query = (
            select(ChatSession.user_id)
            .distinct()
        )

        if user_email:
            email_query = email_query.where(ChatSession.user_id == user_email)

        email_result = await db.execute(email_query)
        user_emails = [row[0] for row in email_result.fetchall()]

        if not user_emails:
            return []

        # Now load users by email
        user_query = (
            select(User)
            .options(selectinload(User.chat_sessions))
            .where(User.email.in_(user_emails))
        )

        result = await db.execute(user_query)
        users = result.scalars().all()

        return users


async def clean_user_memory(user_id: str) -> bool:
    """Delete user's memory document."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memory = result.scalar_one_or_none()
        if memory:
            await db.delete(memory)
            await db.commit()
            logger.info(f"  🗑️  Deleted existing memory for {user_id}")
            return True
        return False


async def extract_memory_for_user(
    user_id: str,
    dry_run: bool,
    force: bool,
    limit: Optional[int] = None,
    clean: bool = False,
) -> Optional[str]:
    """
    Run memory extraction for a user by processing each session sequentially.

    The memory agent only looks at the last 10 messages per call, so we process
    each session independently and let memory accumulate over time.

    Args:
        user_id: User email
        dry_run: If True, don't save to database
        force: If True, re-extract even if memory exists

    Returns:
        Final memory document or None if no changes
    """
    # Clean existing memory if requested
    if clean:
        await clean_user_memory(user_id)

    # Get current memory
    current_memory = await database_service.get_user_memory(user_id)

    if current_memory and not force:
        logger.info(f"  ⏭️  Memory already exists for {user_id} (use --force to re-extract)")
        return None

    # Get all sessions for user, sorted by creation date (oldest first)
    sessions = await database_service.get_user_chat_sessions(user_id)
    if not sessions:
        logger.info(f"  ⚠️  No sessions found for {user_id}")
        return None

    # Sort sessions by created_at (oldest first) to process chronologically
    sessions.sort(key=lambda s: s.get("created_at", ""))

    # Apply limit if specified
    if limit and limit < len(sessions):
        sessions = sessions[:limit]
        logger.info(f"  📂 Processing {len(sessions)} session(s) (limited from total)...")
    else:
        logger.info(f"  📂 Processing {len(sessions)} session(s) chronologically...")

    if dry_run:
        total_messages = 0
        for session_info in sessions:
            session_data = await database_service.get_chat_session(session_info["id"])
            if session_data and session_data.get("messages"):
                msg_count = len(session_data["messages"])
                user_count = sum(1 for m in session_data["messages"] if m.get("role") == "user")
                total_messages += msg_count
                logger.info(f"     📝 '{session_info.get('session_name', 'Untitled')}': {msg_count} msgs ({user_count} user)")
        logger.info(f"  🔍 [DRY RUN] Would process {total_messages} total messages across {len(sessions)} sessions")
        return None

    # Process each session sequentially, accumulating memory
    sessions_processed = 0
    final_memory = current_memory if force else None

    for session_info in sessions:
        session_id = session_info["id"]
        session_name = session_info.get("session_name", "Untitled")

        session_data = await database_service.get_chat_session(session_id)
        if not session_data or not session_data.get("messages"):
            continue

        messages = session_data["messages"]
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            continue

        logger.info(f"     📝 '{session_name}': {len(messages)} msgs ({len(user_messages)} user)")

        # Extract memory for this session (memory agent is a pure function)
        result = await memory_agent.extract(
            messages=messages,
            current_memory=final_memory,
        )

        if result:
            final_memory = result
            # Save to database
            await database_service.save_user_memory(user_id, final_memory)
            sessions_processed += 1

    if final_memory:
        logger.info(f"  ✅ Memory extracted from {sessions_processed} session(s)")
        # Show preview of extracted memory
        preview_lines = final_memory.split('\n')[:10]
        for line in preview_lines:
            logger.info(f"     {line}")
        if len(final_memory.split('\n')) > 10:
            logger.info(f"     ... ({len(final_memory.split(chr(10)))} total lines)")
        return final_memory
    else:
        logger.info(f"  ℹ️  No memory extracted for {user_id}")
        return None


async def main(args: argparse.Namespace) -> int:
    """
    Main entry point.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("🧠 Memory Extraction Script")
    logger.info(f"   Options: dry_run={args.dry_run}, force={args.force}, clean={args.clean}, user={args.user or 'all'}, limit={args.limit or 'none'}")
    logger.info("")

    try:
        # Get users with sessions
        users = await get_users_with_sessions(args.user)

        if not users:
            if args.user:
                logger.error(f"❌ User '{args.user}' not found or has no sessions")
            else:
                logger.info("ℹ️  No users with chat sessions found")
            return 1

        logger.info(f"📋 Found {len(users)} user(s) with sessions")
        logger.info("")

        # Process each user
        success_count = 0
        skip_count = 0
        error_count = 0

        for user in users:
            logger.info(f"👤 Processing: {user.email}")

            try:
                # Extract memory (processes each session sequentially)
                result = await extract_memory_for_user(
                    user_id=user.email,
                    dry_run=args.dry_run,
                    force=args.force,
                    limit=args.limit,
                    clean=args.clean,
                )

                if result:
                    success_count += 1
                else:
                    skip_count += 1

            except Exception as e:
                logger.error(f"  ❌ Error processing {user.email}: {e}", exc_info=True)
                error_count += 1

            logger.info("")

        # Summary
        logger.info("=" * 50)
        logger.info("📊 Summary:")
        logger.info(f"   ✅ Extracted: {success_count}")
        logger.info(f"   ⏭️  Skipped: {skip_count}")
        logger.info(f"   ❌ Errors: {error_count}")

        return 0 if error_count == 0 else 1

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract user memories from chat sessions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without saving to database",
    )
    parser.add_argument(
        "--user",
        type=str,
        help="Process single user by email",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract even if memory already exists",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of sessions to process per user",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing memory before extracting (start fresh)",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)
