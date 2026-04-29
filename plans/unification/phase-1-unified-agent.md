# Phase 1: New UnifiedAgent + Clean Backend

## Goal
One agent, one session type (`"chat"`), zero `session_type` branching. All new sessions go through `UnifiedAgent`. Old sessions stay in DB as archive (not surfaced in UI).

## New Files

```
server/agent-service/agents/unified/
  __init__.py
  agent.py       — UnifiedAgent LangGraph
  prompt.py      — ANALYZE_INTENT_PROMPT, step guidance, general response prompts
  schemas.py     — UnifiedIntentSchema
```

---

## `schemas.py`

### `UnifiedIntentSchema`
```python
from pydantic import BaseModel
from typing import Literal, Optional

class UnifiedIntentSchema(BaseModel):
    intent: Literal[
        "create_recipe",     # user wants a new recipe
        "modify_recipe",     # user wants to change existing recipe
        "start_cooking",     # user wants to start cooking current recipe
        "next_step",         # advance to next cooking step
        "previous_step",     # go back a step
        "set_timer",         # set a cooking timer
        "save_recipe",       # save current recipe to library
        "buy_ingredients",   # shopping list / Instacart link
        "generate_images",   # generate step images for current recipe
        "answer_question",   # cooking/food Q&A
        "general_chat",      # anything else
    ]
    recipe_request: Optional[str] = None     # for create_recipe: what to make
    modification_request: Optional[str] = None  # for modify_recipe: what to change
    question: Optional[str] = None           # for answer_question
    timer_minutes: Optional[int] = None      # for set_timer (if mentioned by user)
    timer_label: Optional[str] = None        # for set_timer
```

### `UnifiedStepGuidanceSchema`
Keep same shape as existing `StepGuidanceResponse` in `kitchen/schemas.py`, but **remove** `ingredients_to_highlight` and `ingredients_to_mark_used` (no separate ingredient list in new UX):
```python
class UnifiedStepGuidanceSchema(BaseModel):
    spoken_response: str          # instruction with bolded ingredients inline
    next_step_prompt: str         # label for the "Done/Next" button
    suggested_timer_minutes: Optional[int] = None
    timer_label: Optional[str] = None
```

**Timer in step event**: `suggested_timer_minutes` and `timer_label` must be included in the `kitchen_step` event payload sent to the frontend (currently stripped). Update `_handle_unified_events` to pass them through:
```python
case "kitchen_step":
    saved_content = {
        "type": "kitchen-step",
        "message": event.data["message"],
        "next_step_prompt": event.data.get("next_step_prompt", "Continue"),
        "timer_minutes": event.data.get("suggested_timer_minutes"),  # ADD
        "timer_label": event.data.get("timer_label"),                # ADD
    }
    await redis_client.send_kitchen_step_message(...)
```
This eliminates the need for a separate `timer` event to trigger the timer button in `CookingStep`.

---

## `agent.py` — UnifiedAgent

### Class structure
```python
from agents.base import BaseAgent, AgentEvent
from agents.recipe_creator.agent import RecipeCreatorAgent
from agents.image_gen.agent import ImageGenAgent

class UnifiedAgent(BaseAgent):
    def __init__(self):
        self.recipe_creator = RecipeCreatorAgent()
        self.image_gen = ImageGenAgent()
        self.llm = ChatOpenAI(model="gpt-4o-mini", ...)
        self.graph = self._build_graph()
```

### LangGraph node map
```
analyze_intent
  ├─ create_recipe / modify_recipe  → recipe_subgraph  → proactive_offer → END
  ├─ start_cooking                  → step_action → respond → END
  ├─ next_step                      → step_action → respond → END
  ├─ previous_step                  → step_action → respond → END
  ├─ set_timer                      → timer_node → respond → END
  ├─ save_recipe                    → save_node → respond → END
  ├─ buy_ingredients                → shopping_list → respond → END
  ├─ generate_images                → image_gen_subgraph → END
  ├─ answer_question                → question_node → respond → END
  └─ general_chat                   → respond → END
```

### `recipe_subgraph` node
Delegate to `RecipeCreatorAgent.run_streaming()` and pass all events through unchanged:
```python
async def _recipe_subgraph(self, state):
    async for event in self.recipe_creator.run_streaming(
        message=state["message"],
        message_history=state["message_history"],
        session_id=state["session_id"],
        session_data=state["session_data"],
    ):
        yield event  # pass through: metadata, ingredients, steps, nutrition, text, selector
    # After recipe complete, fall through to proactive_offer node
```

### `proactive_offer` node
Emitted as a `selector` event after recipe creation/modification completes:
```python
yield UnifiedEvent(type="selector", data={
    "message": "Your recipe is ready! What would you like to do next?",
    "options": [
        {"text": "Start Cooking",    "description": "Get step-by-step guidance"},
        {"text": "Save Recipe",      "description": "Save to your recipe library"},
        {"text": "Buy Ingredients",  "description": "Get a shopping list"},
    ],
    "message_id": f"offer-{session_id}-{uuid4().hex[:8]}"
})
```

### `step_action` node
Mirrors existing `KitchenAgent` step logic but instruction text uses inline bold format.
Key: the `GENERATE_STEP_GUIDANCE_PROMPT` must instruct the model to bold ingredient quantities inline.

### `image_gen_subgraph` node
Delegate to `ImageGenAgent`:
```python
async for event in self.image_gen.run_streaming(
    message=state["message"],
    message_history=state["message_history"],
    session_id=state["session_id"],
    session_data=state["session_data"],
):
    yield event
```

### `generate_greeting` signature
```python
async def generate_greeting(self, recipe_name: str = None, **kwargs) -> str:
    # Returns a warm, neutral greeting
    # If recipe_name provided: "Ready to cook {recipe_name}? Let's get started!"
    # Otherwise: one of several GREETING_TIPS (same pattern as existing agents)
```

### Event type
```python
@dataclass
class UnifiedEvent(AgentEvent):
    type: Literal[
        "text", "thinking", "session_name",
        "recipe_update",        # from recipe_subgraph pass-through
        "kitchen_step",         # cooking step guidance
        "timer",                # set timer
        "selector",             # proactive offer / suggestions
        "save_complete",        # recipe saved
        "shopping_list",        # ingredients for buying
        "cooking_complete",     # all steps done
        "complete",             # end of response stream
        "step_image",           # from image_gen pass-through
    ]
    data: Any
```

### `session_data` fields read by UnifiedAgent
Same as KitchenAgent — all fields must be present:
- `session_data["recipe"]` — current WIP recipe dict (or None)
- `session_data["agent_state"]` — `{"current_step": int, "completed_steps": list}`
- `session_data["user_memory"]` — user preferences markdown string
- `session_data["user_id"]` — for memory extraction on completion
- `session_data["recipe_id"]` — reference to saved recipe (if any)

---

## `prompt.py`

### `ANALYZE_INTENT_PROMPT`
Based on `ANALYZE_INTENT_PROMPT` in `kitchen/prompt.py`, extended with new intents:
- `save_recipe` — "user explicitly asks to save the recipe"
- `buy_ingredients` — "user wants to get ingredients, buy groceries, create a shopping list"
- `generate_images` — "user asks to generate/create/show images for the recipe steps"
- Update `create_recipe` description to cover cases where no recipe exists yet

### `GENERATE_STEP_GUIDANCE_PROMPT`
Add explicit instruction:
```
IMPORTANT: Bold all ingredient names and quantities directly in the instruction text.
Example: "Add **200g of spaghetti** to the boiling water and cook for **8 minutes**."
Do NOT list ingredients separately — they must appear bolded inline only.
```

---

## Files to Modify

### `server/agent-service/agents/registry.py`

Current (55 lines):
```python
if session_type not in ("kitchen", "recipe-creator"):
    ...
if session_type == "kitchen":
    agent = KitchenAgent()
else:
    agent = RecipeCreatorAgent()
```

New:
```python
from .unified.agent import UnifiedAgent

async def get_agent(session_type: str = "chat") -> UnifiedAgent:
    if "default" not in _agent_instances:
        logger.info("🔄 Creating UnifiedAgent")
        _agent_instances["default"] = UnifiedAgent()
    return _agent_instances["default"]

def clear_agent_cache():
    global _agent_instances
    _agent_instances = {}
```
Remove `KitchenAgent` and `RecipeCreatorAgent` imports from this file (they remain imported inside `unified/agent.py`).

### `server/agent-service/main.py`

**`/agent/greeting` endpoint** (currently ~30 lines with isinstance checks):
- Remove `isinstance(agent, KitchenAgent)` / `isinstance(agent, RecipeCreatorAgent)` branches
- Call `agent.generate_greeting(recipe_name=recipe_name)` directly (UnifiedAgent supports `recipe_name` kwarg)
- Return format stays the same: `{"greeting": str, "message_type": str, "next_step_prompt": Optional[str]}`

**`/agent/chat` endpoint**:
- Remove `isinstance` dispatch
- Remove `_handle_recipe_creator_events` function entirely
- Rename `_handle_kitchen_events` to `_handle_unified_events`
- Update event type matching in `_handle_unified_events` to cover all `UnifiedEvent` types

**`_handle_unified_events` changes** (currently `_handle_kitchen_events`, ~160 lines):
- **Add** `"save_complete"` case:
  ```python
  case "save_complete":
      recipe = session_data.get("recipe")
      if recipe:
          saved = await database_service.save_recipe(request.session_id, recipe)
          await redis_client.publish(request.session_id, {
              "type": "agent_message",
              "content": {"type": "recipe_saved", "recipe_id": saved["id"]}
          })
  ```
- **Add** `"shopping_list"` case → publish ingredient list to Redis for Instacart link / display
- **Add** recipe pass-through cases from `RecipeCreatorAgent`: `"metadata"`, `"ingredients"` (recipe parts), `"steps"`, `"nutrition"` — these are currently only handled in `_handle_recipe_creator_events` and must be merged in
- **Update** `"kitchen_step"` case to include `timer_minutes` and `timer_label` in the saved content and Redis message
- **Keep**: `"thinking"`, `"text"`, `"kitchen_step"`, `"selector"`, `"session_name"`, `"recipe_created"`, `"agent_state"`, `"cooking_complete"`, `"step_image"`, `"complete"`
- **Remove**: `"ingredients_highlight"`, `"ingredients_set"` (no separate ingredient list in new UX)
- **Remove**: `"timer"` as separate event — timer info is now embedded in `kitchen_step`

### `server/app/main.py` (WebSocket handler)

**Line 500** — greeting recipe preload check:
```python
# Before:
if recipe_id and session_type == "kitchen":
# After:
if recipe_id and session_type in ("kitchen", "chat"):
```

**Lines 488-490** — session_type default:
```python
# Before:
session_type = session_data.get("session_type", "recipe-creator")
# After:
session_type = session_data.get("session_type", "chat")
```

The content-type routing in `handle_ingredients_message`, `handle_recipe_update_message`, `handle_session_name_message` is content-based and requires no changes.

### `server/app/routes/models.py` (or wherever `CreateSessionRequest` is defined)

Find and update the session type field:
```python
# Before (likely):
session_type: str = "recipe-creator"
# After:
session_type: str = "chat"
```

---

## What Stays Unchanged
- `RecipeCreatorAgent` class and its LangGraph — imported internally by `UnifiedAgent`
- `ImageGenAgent` — imported internally by `UnifiedAgent`
- `KitchenAgent` — leave in place for Phase 4 deletion
- All DB models — `session_type = "chat"` stores as `String(50)`, no migration
- Redis pub/sub message format and channel naming (`session:{session_id}`)
- WebSocket content-type routing in `app/main.py`
- `/agent/extract-memory` endpoint — unchanged

---

## Verification

```bash
# 1. Session creation
curl -X POST http://localhost:8000/api/chat-sessions \
  -H "Content-Type: application/json" \
  -b "session=..." \
  -d '{"session_type": "chat"}'
# Expect: 200 with session.id

# 2. Connect WebSocket, receive greeting
# wscat -c ws://localhost:8000/ws/chat/{session_id}
# Send: {"type": "client_ready"}
# Expect: agent_message with type "text" greeting

# 3. Recipe creation
# Send: {"type": "user_message", "content": {"type": "text", "content": "I want to make tacos"}}
# Expect: sequence of recipe_update events, then selector with Save/Cook/Buy

# 4. Start cooking
# Send: {"type": "user_message", "content": {"type": "text", "content": "start cooking"}}
# Expect: kitchen_step with bolded ingredients in message text

# 5. Image generation
# Send: {"type": "user_message", "content": {"type": "text", "content": "generate images"}}
# Expect: step_image events
```
