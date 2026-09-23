# Agent System Reference

All agents live in `server/agent-service/agents/`. They implement `BaseAgent` and yield `AgentEvent` objects via `run_streaming()`. Events are consumed by `agent-service/main.py`, published to Redis, and forwarded to the frontend via WebSocket.

---

## BaseAgent

**File:** `server/agent-service/agents/base.py`

```python
@dataclass
class AgentEvent:
    type: str   # event type string
    data: Any   # payload — type-specific

class BaseAgent(ABC):
    async def run_streaming(...) -> AsyncGenerator[AgentEvent, None]: ...
```

---

## Unified Agent

**Files:** `agents/unified/agent.py`, `agents/unified/schemas.py`, `agents/unified/prompt.py`

The main orchestrator. Receives every user message and routes to the right handler based on intent.

### Intents

| Intent | Handler | Description |
|--------|---------|-------------|
| `create_recipe` | `_handle_recipe_creation` | Delegates to RecipeCreatorAgent |
| `modify_recipe` | `_handle_recipe_creation` | Regenerates changed fields via RecipeCreatorAgent |
| `start_cooking` | `_handle_step_action` | Starts kitchen mode at step 0 |
| `next_step` | `_handle_step_action` | Advances to next step |
| `previous_step` | `_handle_step_action` | Goes back one step |
| `set_timer` | `_handle_timer` | Sets a cooking timer |
| `save_recipe` | `_handle_save_recipe` | Saves session recipe to DB |
| `buy_ingredients` | `_handle_shopping_list` | Generates shopping list |
| `generate_images` | `_handle_generate_images` | Triggers image generation for all steps |
| `answer_question` | `_handle_question` | Answers follow-up questions |
| `general_chat` | `_handle_question` | General conversation |

### Events emitted

| Event type | Data shape | When |
|------------|-----------|------|
| `text` | `{content: str, message_id: str}` | Any text response |
| `thinking` | `{content: str}` | Processing status indicator |
| `metadata` | `{name, description, difficulty, total_time_minutes, servings, tags}` | Recipe metadata ready |
| `ingredients` | `List[{name, amount, unit, eng_name, group}]` | Ingredient list ready |
| `steps` | `List[{instruction, duration, image_description, image_url, group}]` | Step list ready |
| `equipment` | `List[str]` | Equipment list ready (emitted with `steps`) |
| `nutrition` | `{calories, carbs, fats, proteins}` | Nutrition data ready |
| `session_name` | `str` | Session should be renamed (see Session naming below) |
| `recipe_created` | Full recipe dict | Complete recipe assembled |
| `selector` | `{message: str, options: [{text, description}], message_id: str}` | Clickable option buttons |
| `kitchen_step` | `{content: str, step_index: int, total_steps: int, next_step_prompt: str, image_url?: str}` | Step guidance |
| `agent_state` | `{current_step: int}` | Kitchen step position update |
| `cooking_complete` | `null` | All steps finished |
| `save_complete` | `{recipe: Recipe}` | Recipe saved to DB |
| `shopping_list` | `{items: List[str], message: str}` | Shopping list |
| `generate_images` | `{message_id: str}` | Trigger frontend image generation flow |

### Key schemas (`agents/unified/schemas.py`)

- `UnifiedIntentSchema` — intent classification result, plus an optional `session_name` (see below)
- `RecipeReadySchema` — "Start cooking / Explore recipe" offer after recipe creation
- `UnifiedStepGuidanceSchema` — kitchen step guidance with next_step_prompt

### Timers

Step guidance may suggest a timer for passive waits. `MAX_SUGGESTED_TIMER_MINUTES` (120) in
`agents/unified/agent.py` caps this: longer waits — overnight chilling, marinating, proofing —
still appear in the step text but are stripped of the countdown, since an 8-hour in-app timer is
useless. The prompt says the same thing; the constant is the backstop. Timers the user explicitly
asks for (`set_timer`) are never capped.

### Session naming

Recipe sessions are named after the recipe by `RecipeCreatorAgent`. Conversations that never produce
a recipe are named by the unified agent instead, so they don't sit at "Untitled Session" forever.

`UnifiedIntentSchema` carries an optional `session_name`, filled during the intent-classification
call that already runs every turn — so naming costs **no extra LLM request**. The model is given the
current title and only proposes a name once the conversation has a real topic (silent on "hi" or
"thanks"). Because it re-evaluates each turn, a session that isn't named immediately gets named as
soon as a topic emerges.

`run_streaming` emits the event only when the title is still `Untitled Session` **and** the intent is
not `create_recipe`/`modify_recipe` — so a user's manual rename is never overwritten, and recipe
flows keep naming priority.

---

## Recipe Creator Agent

**Files:** `agents/recipe_creator/agent.py`, `agents/recipe_creator/schemas.py`, `agents/recipe_creator/prompt.py`

Handles recipe generation via a LangGraph sequential workflow. Used only when unified agent delegates `create_recipe` or `modify_recipe`.

**Domains:** the same agent generates both food dishes and cocktails/drinks. There is no domain flag or separate agent — the prompts cover both, and the LLM adapts units (`oz`/`ml`/`dashes` vs `cups`/`tbsp`), technique vocabulary (shake/stir/strain vs sear/simmer), and serving counts based on what the user asked for. Cocktails are categorized by an LLM-generated `cocktail` tag, not a schema field.

**Batched / make-ahead drinks:** asking for a pitcher or party batch produces a make-ahead recipe —
mixed in a vessel, chilled, with ice, rim and garnish kept in the serving steps at the end. The
ingredients prompt adds **water at ~20% of the liquid volume**, because a batch that is stirred once
and later poured over ice never picks up the dilution that shaking each drink individually would
provide, and would otherwise taste harsh. Single-serving drinks get no added water.

### LangGraph Workflow

```
                    ┌→ suggest → format_response → END
                    ├→ ask     → format_response → END
analyze → route ───┤→ generate_images → END
                    ├→ modify → check ──┐
                    └→ recipe → check ──┘
                                  │
                         ┌────────┴────────┐
                     generate           complete
                         │                 │
                    gen_metadata        final → END
                         │
                    gen_ingredients
                         │
                    gen_steps
                         │
                    gen_nutrition → check (loops back)
```

| Node | Routes to | Events yielded |
|------|-----------|----------------|
| `analyze` | suggest / ask / recipe / modify / generate_images | — |
| `suggest` | format_response → END | `selector` |
| `ask` | format_response → END | `selector` or `text` |
| `format_response` | END | — |
| `generate_images` | END | `generate_images` |
| `modify` | check | `thinking` |
| `check` | gen_metadata (if incomplete) or final (if complete) | `thinking` |
| `gen_metadata` | gen_ingredients | `session_name`, `metadata`, `thinking` |
| `gen_ingredients` | gen_steps | `ingredients`, `thinking` |
| `gen_steps` | gen_nutrition | `steps`, `equipment`, `thinking` |
| `gen_nutrition` | check (loops back) | `nutrition`, `thinking` |
| `final` | END | `selector` (suppressed by unified agent) |

The unified agent **suppresses** the `selector` from the `final` node and emits its own "Start cooking / Explore recipe" offer after `recipe_created`.

### Key schemas (`agents/recipe_creator/schemas.py`)

```python
class Ingredient(BaseModel):
    name: str
    amount: Optional[str]
    unit: Optional[str]
    eng_name: Optional[str]     # English name for Instacart search
    group: Optional[str]        # Component group for multi-part recipes

class Step(BaseModel):
    instruction: str
    duration_minutes: Optional[int]
    image_description: str      # Always in English — used for image gen + caching
    group: Optional[str]        # Must match ingredient group names exactly

class RecipeSteps(BaseModel):
    steps: List[Step]
    equipment: List[str]        # Tools/glassware, derived from the steps in the same LLM call

class RecipeMetadata(BaseModel):
    name: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    total_time_minutes: int
    servings: int
    tags: List[str]

class RecipeNutrition(BaseModel):
    calories: int   # total for full recipe
    carbs: int      # grams
    fats: int       # grams
    proteins: int   # grams
```

### Equipment
`equipment` is generated inside the `gen_steps` call (it is a field on `RecipeSteps`, not a separate node), so it is always derived from — and consistent with — the steps just written. It is cleared together with `steps` when a modification targets steps, and it is deliberately excluded from `_check_completeness` / `_route_generation` so recipes saved before the field existed do not loop through regeneration. The `equipment` event is emitted even when the list is empty, so the UI clears stale equipment from a previous version of the recipe.

### Grouping (multi-component recipes)
The `group` field on `Ingredient` and `Step` enables sectioned display (e.g., "Caramel layer", "Flan layer" for chocoflan). The agent generates matching group names when a recipe has distinct components. The UI groups items under subheadings. Step badges use sequential global numbering; the flat array index is preserved for image generation.

---

## Memory Agent

**Files:** `agents/memory/agent.py`, `agents/memory/prompt.py`

Extracts user preferences from conversations and stores them in `user_memories`.

- Triggered asynchronously after each recipe save (fire-and-forget)
- Reads conversation history
- Extracts: dietary restrictions, skill level, cuisine preferences, disliked ingredients
- Inserts into `user_memories` table via DB service
- Loaded at the start of each agent session and injected into prompts as `{user_memory}`
- Can be wiped via `DELETE /api/user/memory`

---

## Image Gen Agent

**Files:** `agents/image_gen/agent.py`, `agents/image_gen/schemas.py`, `agents/image_gen/prompt.py`

Generates images for recipe steps on demand.

- Triggered by `generate_images` intent or frontend calling `POST /api/chat-sessions/{id}/steps/{index}/generate-image`
- Uses `image_description` field from each step (always written in English)
- Calls FAL.ai via `services/fal_client.py`
- Uploads result to Google Cloud Storage via `services/gcs_storage.py`
- Checks `step_image_cache` before generating (semantic similarity via embedding)
- Returns `image_url` stored in `step_image_cache` and updated on the step in session recipe JSON

---

## Session Types

| Type | Status | Agent behavior |
|------|--------|---------------|
| `chat` | **Current** | Unified agent handles all intents: recipe creation, cooking, Q&A |
| `recipe-creator` | Legacy | Previously dedicated to recipe creation only |
| `kitchen` | Legacy | Previously dedicated to step-by-step cooking guidance |

---

## Prompt Files

| File | Contents |
|------|----------|
| `agents/unified/prompt.py` | INTENT_ANALYSIS, GREETING, RECIPE_READY, SAVE_RECIPE, SHOPPING_LIST, COOKING_COMPLETE, STEP_GUIDANCE, NO_RECIPE, TIMER prompts |
| `agents/recipe_creator/prompt.py` | ANALYZE_REQUEST, GENERATE_METADATA, GENERATE_INGREDIENTS, GENERATE_STEPS, GENERATE_NUTRITION, SUGGEST_DISHES, ASK_QUESTION, FINAL_RESPONSE, FORMAT_RESPONSE, GREETING prompts |
| `agents/memory/prompt.py` | Memory extraction prompt |
| `agents/image_gen/prompt.py` | Image description refinement prompt |
