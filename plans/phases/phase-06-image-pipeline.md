# Phase 6: Image Orchestration Pipeline

This is the main integration phase — it connects embedding service, image-gen, fal.ai, GCS, and the DB cache.

## Checklist

- [ ] Create `server/agent-service/services/__init__.py`
- [ ] Create `server/agent-service/services/image_pipeline.py`
- [ ] Add `find_similar_step_image`, `save_step_image_cache`, and `update_step_image_url` to `server/app/services.py`
- [ ] Verify pipeline logic with mocked services
- [ ] Commit

## New files

```
server/agent-service/services/
  __init__.py           # Empty file
  image_pipeline.py     # Main orchestration (this phase)
  fal_client.py         # (Phase 4)
  gcs_storage.py        # (Phase 5)
```

### `image_pipeline.py` — Full implementation

```python
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

        Args:
            session_id: Chat session ID (for Redis publishing)
            steps: List of step dicts from recipe_data, each has "instruction" and "image_description"
            recipe_name: Recipe name for prompt context

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
                # Continue with remaining steps — don't let one failure stop all

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
```

## Database methods to add — `server/app/services.py`

Add these methods to the existing `DatabaseService` class. Follow the existing pattern of `async with AsyncSessionLocal() as db:` with try/except/rollback.

The class already imports from `server/app/database.py` (`AsyncSessionLocal`) and all models from `server/app/models/__init__.py`. You'll need to add the `StepImageCache` import and `from pgvector.sqlalchemy import Vector` at the top if needed for raw queries.

```python
async def find_similar_step_image(
    self,
    normalized_text: str,
    embedding: list[float],
    aspect_ratio: str = "1:1",
    threshold: float = 0.92,
) -> Optional[str]:
    """
    Find a cached step image by exact text match or vector similarity.

    Strategy:
    1. Exact match on normalized_text + aspect_ratio (fast path, uses B-tree index)
    2. If no exact match, vector similarity search (uses HNSW index)

    Returns image_url if found, None otherwise. Increments usage_count on hit.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fast path: exact text match
            result = await db.execute(
                select(StepImageCache)
                .where(StepImageCache.normalized_text == normalized_text)
                .where(StepImageCache.aspect_ratio == aspect_ratio)
                .limit(1)
            )
            cached = result.scalar_one_or_none()

            if cached:
                cached.usage_count += 1
                cached.last_used_at = datetime.utcnow()
                await db.commit()
                return cached.image_url

            # Slow path: vector similarity search
            # cosine distance < (1 - threshold) means similarity > threshold
            distance_threshold = 1.0 - threshold
            result = await db.execute(
                select(StepImageCache)
                .where(StepImageCache.aspect_ratio == aspect_ratio)
                .where(StepImageCache.embedding.cosine_distance(embedding) < distance_threshold)
                .order_by(StepImageCache.embedding.cosine_distance(embedding))
                .limit(1)
            )
            cached = result.scalar_one_or_none()

            if cached:
                cached.usage_count += 1
                cached.last_used_at = datetime.utcnow()
                await db.commit()
                return cached.image_url

            return None

        except Exception as e:
            await db.rollback()
            logger.error(f"Error finding similar step image: {e}", exc_info=True)
            return None


async def save_step_image_cache(
    self,
    normalized_text: str,
    embedding: list[float],
    image_url: str,
    aspect_ratio: str,
    prompt: str,
    model: str,
    generation_time_ms: int,
) -> None:
    """Insert a new entry into the step image cache."""
    async with AsyncSessionLocal() as db:
        try:
            entry = StepImageCache(
                normalized_text=normalized_text,
                embedding=embedding,
                image_url=image_url,
                aspect_ratio=aspect_ratio,
                prompt_used=prompt,
                model_used=model,
                generation_time_ms=generation_time_ms,
            )
            db.add(entry)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving step image cache: {e}", exc_info=True)


async def update_step_image_url(
    self,
    session_id: str,
    step_index: int,
    image_url: str,
) -> bool:
    """
    Update image_url for a specific step in session.recipe.steps[step_index].

    The recipe is stored as JSON in chat_sessions.recipe column.
    Follow the same pattern as save_or_update_recipe() in this file (around line 625).
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session or not session.recipe:
                return False

            recipe = session.recipe
            steps = recipe.get("steps", [])

            if step_index < 0 or step_index >= len(steps):
                return False

            steps[step_index]["image_url"] = image_url
            recipe["steps"] = steps

            session.recipe = recipe
            flag_modified(session, "recipe")
            session.updated_at = datetime.utcnow()

            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating step image URL: {e}", exc_info=True)
            return False
```

## Verification

- Run with mocked services to verify the pipeline logic
- Check DB for cache entries after generation
- Run a second time with same steps — verify cache hits in logs

## Commit
```
feat: add image orchestration pipeline with cache, generation, and storage
```
