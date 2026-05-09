import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request

from ..services import database_service
from .recipes import get_current_user_with_storage
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user_with_storage)):
    """Get user profile including memory and preferences"""
    user_email = current_user.get("email")

    memory, metadata = await asyncio.gather(
        database_service.get_user_memory(user_email),
        database_service.get_user_metadata(user_email),
    )

    return {
        "user": {
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "picture": current_user.get("picture"),
        },
        "memory": memory,
        "language": metadata.get("language", "English"),
    }


@router.patch("/preferences")
async def update_preferences(
    request: Request,
    current_user: dict = Depends(get_current_user_with_storage),
):
    """Update a user preference stored in user_metadata"""
    body = await request.json()
    key = body.get("key")
    value = body.get("value")
    if not key:
        raise HTTPException(status_code=400, detail="Missing key")
    await database_service.update_user_metadata(current_user["email"], key, value)
    return {"ok": True}


@router.delete("/memory")
async def delete_memory(current_user: dict = Depends(get_current_user_with_storage)):
    """Wipe the user's accumulated memory document"""
    await database_service.clear_user_memory(current_user["email"])
    return {"ok": True}
