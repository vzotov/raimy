"""Pydantic schemas for structured LLM outputs in image generation agent"""

from pydantic import BaseModel, Field


class StepImagePrompt(BaseModel):
    """LLM-generated prompt for a single recipe step."""

    step_index: int = Field(description="Zero-based index of the recipe step")
    prompt: str = Field(
        description=(
            "A detailed, FLUX-optimized image generation prompt for this cooking step. "
            "50-80 words describing the scene vividly: specific ingredients visible, "
            "cooking action, colors, textures, cooking vessel, camera angle, lighting. "
            "No people, hands, or human body parts."
        )
    )


class ImagePrompts(BaseModel):
    """Batch of LLM-generated prompts for all recipe steps."""

    prompts: list[StepImagePrompt]
