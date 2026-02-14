"""fal.ai fallback client for image generation when local GPU is unavailable."""
import os
import logging

import httpx

logger = logging.getLogger(__name__)

FAL_API_URL = "https://fal.run/fal-ai/flux/schnell"


class FalImageClient:
    """Generates images via fal.ai FLUX schnell API as fallback."""

    def __init__(self):
        self.api_key = os.getenv("FAL_KEY")
        if not self.api_key:
            logger.warning("FAL_KEY not set - fal.ai fallback will not work")

    async def generate(self, prompt: str, width: int = 1024, height: int = 1024) -> bytes:
        """
        Generate image via fal.ai FLUX schnell.

        Returns:
            PNG image bytes

        Raises:
            Exception: If generation fails after retries
        """
        if not self.api_key:
            raise RuntimeError("FAL_KEY not configured")

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_inference_steps": 4,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(3):
                try:
                    response = await client.post(FAL_API_URL, json=payload, headers=headers)
                    response.raise_for_status()
                    result = response.json()

                    # Download the generated image
                    image_url = result["images"][0]["url"]
                    image_response = await client.get(image_url)
                    image_response.raise_for_status()

                    logger.info(f"fal.ai generated image: {width}x{height}, attempt {attempt + 1}")
                    return image_response.content

                except Exception as e:
                    logger.warning(f"fal.ai attempt {attempt + 1}/3 failed: {e}")
                    if attempt == 2:
                        raise

        raise RuntimeError("fal.ai generation failed after 3 attempts")
