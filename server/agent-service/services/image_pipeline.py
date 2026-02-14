"""
Image generation pipeline for recipe steps.

Orchestrates: embedding service -> cache lookup -> image generation -> GCS upload -> cache storage.
Each step image is published to Redis as soon as it's ready for progressive UI updates.
"""
import base64
import logging
import os
import time

import httpx

from app.services import database_service
from core.redis_client import get_redis_client
from .fal_client import FalImageClient
from .gcs_storage import GCSStorage

logger = logging.getLogger(__name__)


class StepImagePipeline:
    """Full pipeline: embed -> cache check -> generate -> upload -> cache store -> publish."""

    def __init__(self):
        self.embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8004")
        self.image_gen_url = os.getenv("IMAGE_GEN_SERVICE_URL", "http://localhost:8005")
        self.gcs = GCSStorage()
        self.fal_client = FalImageClient()
        self.redis_client = get_redis_client()
        self.similarity_threshold = 0.92
        self.aspect_ratio = "1:1"
        self.width = 1024
        self.height = 1024

    async def generate_step_images(
        self,
        session_id: str,
        steps: list[dict],
        recipe_name: str,
    ) -> list[dict]:
        """
        Generate images for all recipe steps. Publishes each result to Redis as it completes.

        Returns:
            List of {"step_index": int, "image_url": str} for successfully generated images
        """
        results = []

        for index, step in enumerate(steps):
            try:
                image_description = step.get("image_description")
                if not image_description:
                    logger.warning(f"Step {index} has no image_description, skipping")
                    continue

                image_url = await self._process_single_step(image_description)

                if image_url:
                    results.append({"step_index": index, "image_url": image_url})

                    # Publish to Redis immediately for progressive UI update
                    await self.redis_client.send_step_image_message(
                        session_id, index, image_url
                    )

            except Exception as e:
                logger.error(f"Failed to generate image for step {index}: {e}")

        return results

    async def _process_single_step(self, image_description: str) -> str | None:
        """
        Process a single step: embed -> cache check -> generate -> upload -> cache store.
        Returns image URL or None on failure.
        """
        # 1. Get embedding
        embedding = await self._get_embedding(image_description)
        if not embedding:
            return None

        # 2. Check cache (exact match first, then vector similarity)
        cached_url = await database_service.find_similar_step_image(
            normalized_text=image_description.lower().strip(),
            embedding=embedding,
            aspect_ratio=self.aspect_ratio,
            threshold=self.similarity_threshold,
        )
        if cached_url:
            logger.info(f"Cache HIT: '{image_description[:50]}...'")
            return cached_url

        # 3. Generate image
        logger.info(f"Cache MISS: generating for '{image_description[:50]}...'")
        prompt = self._build_image_prompt(image_description)
        image_bytes, model_used, gen_time_ms = await self._generate_image(prompt)
        if not image_bytes:
            return None

        # 4. Upload to GCS
        image_url = self.gcs.upload_image(image_bytes, image_description, self.aspect_ratio)

        # 5. Store in cache
        await database_service.save_step_image_cache(
            normalized_text=image_description.lower().strip(),
            embedding=embedding,
            image_url=image_url,
            aspect_ratio=self.aspect_ratio,
            prompt=prompt,
            model=model_used,
            generation_time_ms=gen_time_ms,
        )

        return image_url

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Get embedding from embedding service."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.embedding_url}/embed",
                    json={"texts": [text]},
                )
                response.raise_for_status()
                return response.json()["embeddings"][0]
        except Exception as e:
            logger.error(f"Embedding service error: {e}")
            return None

    async def _generate_image(self, prompt: str) -> tuple[bytes | None, str, int]:
        """
        Try local image-gen service, fallback to fal.ai.
        Returns: (image_bytes, model_used, generation_time_ms)
        """
        # Try local first
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.image_gen_url}/generate",
                    json={
                        "prompt": prompt,
                        "width": self.width,
                        "height": self.height,
                    },
                )
                response.raise_for_status()
                data = response.json()
                image_bytes = base64.b64decode(data["image_base64"])
                return image_bytes, "flux-schnell-local", data.get("inference_time_ms", 0)
        except Exception as e:
            logger.warning(f"Local image-gen unavailable ({e}), trying fal.ai fallback")

        # Fallback to fal.ai
        try:
            start = time.perf_counter()
            image_bytes = await self.fal_client.generate(prompt, self.width, self.height)
            gen_time = int((time.perf_counter() - start) * 1000)
            return image_bytes, "fal-flux-schnell", gen_time
        except Exception as e:
            logger.error(f"fal.ai fallback also failed: {e}")
            return None, "", 0

    def _build_image_prompt(self, image_description: str) -> str:
        """Build FLUX-optimized food photography prompt from LLM image_description."""
        return (
            f"A cooking scene: {image_description}. "
            "Style: food photography, warm natural lighting, "
            "shallow depth of field, overhead angle, "
            "clean professional kitchen, appetizing presentation"
        )
