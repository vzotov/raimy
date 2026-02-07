from fastapi import APIRouter, Depends

from ..services import database_service
from .recipes import get_current_user_with_storage
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user_with_storage)):
    """Get user profile including memory"""
    user_email = current_user.get("email")

    # Get user memory
    memory = await database_service.get_user_memory(user_email)

    return {
        "user": {
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "picture": current_user.get("picture"),
        },
        "memory": memory,
    }
