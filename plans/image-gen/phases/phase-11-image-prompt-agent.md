# Phase 11: Image Generation Agent

## Checklist

- [x] Create `agents/image_gen/__init__.py`
- [x] Create `agents/image_gen/schemas.py` — `StepImagePrompt` + `ImagePrompts` batch schema
- [x] Create `agents/image_gen/prompt.py` — `GENERATE_IMAGE_PROMPT` batch template
- [x] Create `agents/image_gen/agent.py` — `ImageGenAgent(BaseAgent)` with direct streaming
- [x] Update `main.py` — replace `StepImagePipeline` with `ImageGenAgent`, handle GCS/DB in event loop
- [x] Delete `services/image_pipeline.py`
- [x] Update `plans/STEP_IMAGE_GENERATION.md` — add Phase 11 row
- [ ] End-to-end test: generate recipe, check logs for LLM-generated prompts
- [ ] Verify cache hits on repeat generation
- [ ] Verify GCS uploads and DB cache entries from main.py
- [ ] Commit

## Architecture

```
main.py (_generate_step_images(session_id, recipe_data))
  └─ ImageGenAgent.run_streaming(session_id=session_id, session_data={"recipe": recipe_data})
       1. _generate_all_prompts(recipe) — single LLM call, returns dict[step_index, prompt]
       2. for each step with a generated prompt:
            a. embed prompt
            b. cache check
            c. (hit)  yield ImageGenEvent with image_url
            d. (miss) generate image via local/fal → yield ImageGenEvent with image_bytes
       3. yield ImageGenEvent("complete")

       Events are yielded immediately per step (no batching).

main.py consumes events:
  "step_image" with image_url   → redis publish (cache hit, no persistence needed)
  "step_image" with image_bytes → GCS upload → DB cache save (prompt + embedding + url) → redis publish
  "complete"                    → log
```

## New — `agents/image_gen/schemas.py`

```python
class StepImagePrompt(BaseModel):
    step_index: int   # Zero-based index of the recipe step
    prompt: str       # Detailed FLUX-optimized prompt (50-80 words)

class ImagePrompts(BaseModel):
    prompts: list[StepImagePrompt]  # Batch of all step prompts
```

## New — `agents/image_gen/prompt.py`

`GENERATE_IMAGE_PROMPT` batch template with:
- Recipe name, description, ingredients summary
- Full list of steps to generate (step_index, instruction, visual hint) — only steps with `image_description`
- Instructions: vivid food photography, specific colors/textures, camera angle, no hands/people
- Visual progression and consistent style across the full sequence

## New — `agents/image_gen/agent.py`

`ImageGenAgent(BaseAgent)` — no LangGraph, direct async generator for immediate per-step streaming.

**`__init__`:** `ChatOpenAI(model="gpt-5-mini", temperature=0.7)`, embedding URL + image-gen URL from env, `FalImageClient()` only if `FAL_KEY` is set (otherwise `None`), similarity threshold 0.92, 512x512.

**`generate_greeting()`:** returns `""` (background agent, not used).

**`_generate_all_prompts(recipe)`:** Filters steps with `image_description`, formats them into the batch prompt template, calls LLM once with `ImagePrompts` structured output. Returns `dict[int, str]` mapping step_index → prompt.

**`_generate_image(prompt)`:** Calls local image-gen service with 3 retries (exponential backoff: 1s, 2s, 4s). Falls back to fal.ai only if `FAL_KEY` is configured. Returns `(image_bytes, model_used, generation_time_ms)`.

**`run_streaming()`:** calls `_generate_all_prompts()` once, then loops over steps. For each step, embeds prompt, checks cache, generates image if needed, and **yields `ImageGenEvent` immediately** — no collecting into a list. Ends with `ImageGenEvent("complete", None)`.

**Error handling:** Per-step try/except. On failure, log and skip to next step.

## Modify — `main.py`

- Replace `StepImagePipeline` import with `ImageGenAgent`
- `_generate_step_images(session_id, recipe_data)` — iterate agent events
- On `step_image` with `image_bytes` (cache miss):
  - `gcs.upload_image(image_bytes, ...)`
  - `database_service.save_step_image_cache(normalized_text=prompt, embedding=embedding, image_url=..., ...)`
  - `redis_client.send_step_image_message(session_id, step_index, image_url)`
- On `step_image` with `image_url` (cache hit):
  - `redis_client.send_step_image_message(session_id, step_index, image_url)` only
- Call site: pass `recipe_data=recipe_data`

## Delete — `services/image_pipeline.py`

All logic moves into agent (prompt gen, embed, cache, image gen) + main.py (GCS, DB, Redis).

## Key Design Decision

Cache is keyed on the LLM-generated prompt embedding (not the raw `image_description`). The prompt is richer (50-80 words vs 5-10) and contains recipe-specific context.
