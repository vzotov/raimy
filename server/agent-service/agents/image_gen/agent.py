"""
Image Generation Agent

Generates detailed FLUX-optimized prompts via LLM, then produces images
for each recipe step.
"""

import asyncio
import base64
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Literal

import httpx
from langchain_openai import ChatOpenAI

from ..base import AgentEvent, BaseAgent
from .prompt import GENERATE_IMAGE_PROMPT
from .schemas import ImagePrompts
from services.fal_client import FalImageClient
from services.gcs_storage import GCSStorage
from app.services import database_service

logger = logging.getLogger(__name__)


@dataclass
class ImageGenEvent(AgentEvent):
    """
    Event emitted during image generation.

    Event types:
    - "step_image": Image ready for a step (data: {session_id, step_index, prompt, embedding, image_url|image_bytes})
    - "complete": All steps processed (data: None)
    """

    type: Literal["step_image", "complete"]
    data: Any


class ImageGenAgent(BaseAgent):
    """Agent for generating recipe step images with LLM-powered prompts."""

    MODEL = "gpt-5.4-nano"

    def __init__(self):
        self.llm = ChatOpenAI(
            model=self.MODEL,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8004")
        self.image_gen_url = os.getenv("IMAGE_GEN_SERVICE_URL", "http://localhost:8005")
        self.fal_client = FalImageClient() if os.getenv("FAL_KEY") else None
        self.similarity_threshold = 0.92
        self.aspect_ratio = "1:1"
        self.width = 512
        self.height = 512
        logger.info(f"🎨 ImageGenAgent initialized with model: {self.MODEL}")

    async def generate_greeting(self, **kwargs) -> str:
        return ""

    def _format_recipe_context(self, recipe: dict) -> dict:
        """Extract formatted context strings from recipe for the LLM prompt."""
        ingredients = recipe.get("ingredients", [])
        ingredients_summary = ", ".join(
            ing.get("name", "") for ing in ingredients[:10]
        )
        if len(ingredients) > 10:
            ingredients_summary += f" (+{len(ingredients) - 10} more)"

        return {
            "recipe_name": recipe.get("name", "Recipe"),
            "recipe_description": recipe.get("description", ""),
            "ingredients_summary": ingredients_summary or "Not specified",
        }

    async def _generate_all_prompts(self, recipe: dict) -> dict[int, str]:
        """Generate FLUX prompts for all steps in a single LLM call."""
        recipe_context = self._format_recipe_context(recipe)
        steps = recipe.get("steps", [])

        # Build list of steps that have image_description and no image yet
        steps_lines = []
        for i, step in enumerate(steps):
            if step.get("image_url"):
                continue
            image_description = step.get("image_description")
            if not image_description:
                continue
            steps_lines.append(
                f"- step_index: {i}\n"
                f"  Instruction: {step.get('instruction', '')}\n"
                f"  Visual hint: {image_description}"
            )

        if not steps_lines:
            return {}

        prompt = GENERATE_IMAGE_PROMPT.format(
            recipe_name=recipe_context["recipe_name"],
            recipe_description=recipe_context["recipe_description"],
            ingredients_summary=recipe_context["ingredients_summary"],
            steps_to_generate="\n".join(steps_lines),
        )

        llm_with_output = self.llm.with_structured_output(ImagePrompts)
        result: ImagePrompts = await llm_with_output.ainvoke(prompt)

        prompt_map = {sp.step_index: sp.prompt for sp in result.prompts}
        logger.info(f"🎨 Generated {len(prompt_map)} prompts in single LLM call")
        return prompt_map

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
        Generate image via local service (with retries), fal.ai fallback only if FAL_KEY is set.
        Returns: (image_bytes, model_used, generation_time_ms)
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
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
                    return image_bytes, "flux-klein-local", data.get("inference_time_ms", 0)
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(f"Local image-gen attempt {attempt + 1}/{max_retries} failed ({e}), retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    if not self.fal_client:
                        logger.error(f"Local image-gen failed after {max_retries} attempts ({e}), no fal.ai fallback configured")
                        return None, "", 0
                    logger.warning(f"Local image-gen failed after {max_retries} attempts ({e}), trying fal.ai fallback")

        try:
            start = time.perf_counter()
            image_bytes = await self.fal_client.generate(prompt, self.width, self.height)
            gen_time = int((time.perf_counter() - start) * 1000)
            return image_bytes, "fal-flux-schnell", gen_time
        except Exception as e:
            logger.error(f"fal.ai fallback also failed: {e}")
            return None, "", 0

    async def generate_single_step_image(
        self,
        recipe_name: str,
        step_index: int,
        step_instruction: str,
        image_description: str = "",
        recipe_description: str = "",
        ingredients_summary: str = "",
    ) -> str | None:
        """
        Generate an image for a single recipe step.

        Returns the image URL (from cache or newly generated), or None on failure.
        """
        gcs = GCSStorage()

        # Build a single-step entry for the batch prompt generator
        visual_hint = image_description or step_instruction
        steps_lines = (
            f"- step_index: {step_index}\n"
            f"  Instruction: {step_instruction}\n"
            f"  Visual hint: {visual_hint}"
        )

        prompt_text = GENERATE_IMAGE_PROMPT.format(
            recipe_name=recipe_name,
            recipe_description=recipe_description,
            ingredients_summary=ingredients_summary or "Not specified",
            steps_to_generate=steps_lines,
        )

        llm_with_output = self.llm.with_structured_output(ImagePrompts)
        result: ImagePrompts = await llm_with_output.ainvoke(prompt_text)

        if not result.prompts:
            logger.warning(f"🎨 Single step {step_index}: LLM returned no prompts")
            return None

        flux_prompt = result.prompts[0].prompt

        # Embed the prompt
        embedding = await self._get_embedding(flux_prompt)
        if not embedding:
            return None

        # Cache check
        cached_url = await database_service.find_similar_step_image(
            normalized_text=flux_prompt.lower().strip(),
            embedding=embedding,
            aspect_ratio=self.aspect_ratio,
            threshold=self.similarity_threshold,
        )
        if cached_url:
            logger.info(f"🎨 Single step {step_index}: cache HIT")
            return cached_url

        # Generate image
        logger.info(f"🎨 Single step {step_index}: generating image")
        image_bytes, model_used, gen_time_ms = await self._generate_image(flux_prompt)
        if not image_bytes:
            return None

        # Upload to GCS
        image_url = gcs.upload_image(image_bytes, flux_prompt, self.width, self.height)

        # Save to cache
        await database_service.save_step_image_cache(
            normalized_text=flux_prompt.lower().strip(),
            embedding=embedding,
            image_url=image_url,
            aspect_ratio=self.aspect_ratio,
            prompt=flux_prompt,
            model=model_used,
            generation_time_ms=gen_time_ms,
        )

        return image_url

    async def run_streaming(
        self,
        message: str,
        message_history: List[Dict],
        session_id: str,
        session_data: Dict[str, Any],
    ) -> AsyncGenerator[ImageGenEvent, None]:
        """
        Process all recipe steps and yield image events as each completes.

        Recipe data is passed via session_data["recipe"].
        """
        recipe = session_data.get("recipe", {})
        steps = recipe.get("steps", [])
        if not steps:
            yield ImageGenEvent(type="complete", data=None)
            return

        # Generate all prompts in a single LLM call
        prompt_map = await self._generate_all_prompts(recipe)

        for index, step in enumerate(steps):
            try:
                # Skip steps that already have images
                if step.get("image_url"):
                    continue

                prompt = prompt_map.get(index)
                if not prompt:
                    logger.warning(f"Step {index} has no generated prompt, skipping")
                    continue

                # 1. Embed the generated prompt
                embedding = await self._get_embedding(prompt)
                if not embedding:
                    continue

                # 2. Cache check using prompt embedding
                cached_url = await database_service.find_similar_step_image(
                    normalized_text=prompt.lower().strip(),
                    embedding=embedding,
                    aspect_ratio=self.aspect_ratio,
                    threshold=self.similarity_threshold,
                )

                if cached_url:
                    logger.info(f"🎨 Step {index}: cache HIT")
                    yield ImageGenEvent(type="step_image", data={
                        "session_id": session_id,
                        "step_index": index,
                        "prompt": prompt,
                        "embedding": embedding,
                        "image_url": cached_url,
                        "image_bytes": None,
                    })
                    continue

                # 3. Cache miss — generate image
                logger.info(f"🎨 Step {index}: generating image")
                image_bytes, model_used, gen_time_ms = await self._generate_image(prompt)
                if not image_bytes:
                    continue

                yield ImageGenEvent(type="step_image", data={
                    "session_id": session_id,
                    "step_index": index,
                    "prompt": prompt,
                    "embedding": embedding,
                    "image_url": None,
                    "image_bytes": image_bytes,
                    "model_used": model_used,
                    "generation_time_ms": gen_time_ms,
                })

            except Exception as e:
                logger.error(f"🎨 Step {index}: failed: {e}", exc_info=True)

        yield ImageGenEvent(type="complete", data=None)
