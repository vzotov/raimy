# Phase 8: Redis + Backend Message Handling

## Checklist

- [ ] Add `send_step_image_message()` to `server/core/redis_client.py`
- [ ] Add `"set_step_image"` case to `handle_recipe_update_message()` in `server/app/main.py`
- [ ] Verify WebSocket messages arrive in browser devtools
- [ ] Commit

## Modify — `server/core/redis_client.py`

Add a new helper method to the `RedisClient` class (after `send_recipe_nutrition_message` around line 375). Follow the existing pattern:

```python
async def send_step_image_message(self, session_id: str, step_index: int, image_url: str):
    """
    Send step image update to session.

    Args:
        session_id: Session ID
        step_index: Index of the step in the recipe steps array (0-based)
        image_url: Public GCS URL of the generated image
    """
    await self.publish(
        f"session:{session_id}",
        {
            "type": "agent_message",
            "content": {
                "type": "recipe_update",
                "action": "set_step_image",
                "step_index": step_index,
                "image_url": image_url,
            }
        }
    )
```

## Modify — `server/app/main.py`

In the `handle_recipe_update_message()` function (defined around line 388), there's a `match action:` block with cases for `"save_recipe"`, `"set_metadata"`, `"set_ingredients"`, `"set_steps"`, `"set_nutrition"`. Add a new case after `"set_nutrition"` (around line 458):

```python
case "set_step_image":
    # Update individual step image in session recipe
    await database_service.update_step_image_url(
        session_id=session_id,
        step_index=content.get("step_index"),
        image_url=content.get("image_url"),
    )
```

### How the message flow works

The Redis listener in `server/app/main.py` (the `listen_to_redis` background task around line 340) receives ALL messages published to the session channel and:
1. Forwards them to WebSocket (so frontend gets them immediately)
2. Handles specific types for DB persistence (ingredients, recipe updates, session name)

The `set_step_image` case only needs DB persistence — the WebSocket forward is automatic.

## Verification

- Generate a recipe, open browser devtools Network tab (WS filter)
- Watch for `recipe_update` messages with `action: "set_step_image"`
- Each message should have `step_index` and `image_url`

## Commit
```
feat: add Redis and backend message handling for step images
```
