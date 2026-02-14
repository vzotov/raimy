# Phase 7: Trigger — Wire into Recipe Creator Flow

## Checklist

- [ ] Add `StepImagePipeline` import to `server/agent-service/main.py`
- [ ] Add `_generate_step_images()` background task function
- [ ] Modify the `"complete"` case to trigger image generation
- [ ] Add `EMBEDDING_SERVICE_URL` and `IMAGE_GEN_SERVICE_URL` env vars to `docker-compose.yml`
- [ ] Verify image generation triggers after recipe creation
- [ ] Commit

## Modify — `server/agent-service/main.py`

### Add import at top of file (with other imports around line 18-21)

```python
from services.image_pipeline import StepImagePipeline
```

### Add new top-level function (after `_extract_and_save_memory` around line 114)

```python
async def _generate_step_images(session_id: str, steps: list, recipe_name: str):
    """Background task: generate images for all recipe steps."""
    try:
        pipeline = StepImagePipeline()
        results = await pipeline.generate_step_images(session_id, steps, recipe_name)
        logger.info(f"Generated {len(results)} step images for session {session_id}")
    except Exception as e:
        logger.error(f"Step image generation failed: {e}", exc_info=True)
```

### Modify the `"complete"` case in `_handle_recipe_creator_events()` (currently line 400-404)

The current code is:

```python
case "complete":
    # Clear thinking indicator
    await redis_client.send_system_message(
        request.session_id, "thinking", None
    )
```

Change it to:

```python
case "complete":
    # Clear thinking indicator
    await redis_client.send_system_message(
        request.session_id, "thinking", None
    )

    # Trigger image generation in background (like memory extraction)
    if recipe_data.get("steps"):
        asyncio.create_task(
            _generate_step_images(
                session_id=request.session_id,
                steps=recipe_data["steps"],
                recipe_name=recipe_data.get("name", "Recipe"),
            )
        )
```

This follows the exact same `asyncio.create_task()` pattern used for memory extraction in `_handle_kitchen_events()` at line 279 of the same file.

### Add env vars to `docker-compose.yml` agent-service section

```yaml
- EMBEDDING_SERVICE_URL=http://embedding-service:8004
- IMAGE_GEN_SERVICE_URL=${IMAGE_GEN_SERVICE_URL:-http://host.docker.internal:8005}
```

Note: `host.docker.internal` is used because the image-gen service runs outside Docker on the host machine. On Linux, you may need `--add-host=host.docker.internal:host-gateway` in docker-compose.

## Verification

- Generate a recipe via chat
- Check agent-service logs: `docker compose logs -f agent-service`
- Should see "Cache MISS: generating for '...'" and "Generated N step images" messages
- Verify step images appear in session recipe data in the DB

## Commit
```
feat: wire image pipeline into recipe creator complete event
```
