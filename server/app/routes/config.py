import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/features")
async def get_features():
    """
    Get feature flags for the application.

    Returns which optional integrations are enabled based on
    environment configuration.
    """
    return {
        "instacart_enabled": bool(os.getenv("INSTACART_API_KEY")),
        "image_gen_enabled": bool(os.getenv("IMAGE_GEN_ENABLED")),
    }
