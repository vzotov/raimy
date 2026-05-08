"""Prompts for image generation agent"""

GENERATE_IMAGE_PROMPT = """You are an expert food photography prompt engineer for AI image 
generation (FLUX klein model).

Given a recipe and its steps, write a detailed image generation prompt for EACH step listed below.

## Recipe Context
Recipe: {recipe_name}
Description: {recipe_description}
Key ingredients: {ingredients_summary}

## Steps to Generate Prompts For
{steps_to_generate}

## Requirements
For EACH step above, write a prompt (80-150 words) that:
- Describes the specific cooking action and visible ingredients for that step
- Uses food photography style: warm natural lighting, shallow depth of field
- Specifies camera angle (overhead, close-up, 45-degree, etc.)
- Mentions specific colors, textures, and cooking vessels relevant to that step
- Shows visual progression across the full sequence (raw → prep → cooking → plating)
- Maintains a consistent visual style and color palette across all prompts
- NEVER includes people, hands, fingers, or any human body parts
- Focuses on ingredients, utensils, and the cooking process only

Return one prompt per step using the step_index provided."""
