# Phase 9: Schema Changes — Add `image_description` and `image_url` to Steps

## Checklist

- [x] Add `image_description` field to Step schema in `server/agent-service/agents/recipe_creator/schemas.py`
- [x] Update `GENERATE_STEPS_PROMPT` in `server/agent-service/agents/recipe_creator/prompt.py`
- [x] Add `image_description` and `image_url` to `RecipeStepModel` in `server/app/services.py`
- [x] Add `image_description` and `image_url` to `RecipeStep` in `client/src/types/recipe.ts`
- [x] Add `RecipeStepImageUpdate` type to `client/src/types/chat-message-types.ts`
- [x] Add `SET_STEP_IMAGE` reducer action to `client/src/hooks/useMealPlannerRecipe.ts`
- [ ] Verify LLM generates `image_description` for each step (requires full e2e test)
- [x] Commit

## Backend

### `server/agent-service/agents/recipe_creator/schemas.py` — Step model (currently line 81-87)

Current:
```python
class Step(BaseModel):
    instruction: str = Field(description="Step instruction")
    duration_minutes: Optional[int] = Field(
        default=None, description="Estimated duration in minutes"
    )
```

Change to:
```python
class Step(BaseModel):
    instruction: str = Field(description="Step instruction")
    duration_minutes: Optional[int] = Field(
        default=None, description="Estimated duration in minutes"
    )
    image_description: str = Field(
        description="Short visual description of this step for image generation and caching. "
        "Describe the cooking action and key visible elements without quantities or timing. "
        "Examples: 'dicing onions finely on a cutting board', "
        "'combining flour salt and eggs in a mixing bowl'"
    )
```

**Important**: `image_description` is a required field (not Optional). This schema is used with `llm.with_structured_output(RecipeSteps)` in `_generate_steps()` (line 613 of agent.py), so the LLM will be forced to produce it for every step. The field description serves as the LLM instruction.

**Do NOT add `image_url` to this schema** — it's populated by the image pipeline after generation, not by the LLM. The `image_url` only appears in the JSON stored in the DB.

### `server/agent-service/agents/recipe_creator/prompt.py` — Update `GENERATE_STEPS_PROMPT` (line 116)

Add `image_description` to the output instructions:

Current:
```
Create clear, actionable cooking steps:
- instruction: One clear action per step (start with a verb)
- duration_minutes: Time for steps that require waiting (optional)
```

Change to:
```
Create clear, actionable cooking steps:
- instruction: One clear action per step (start with a verb)
- duration_minutes: Time for steps that require waiting (optional)
- image_description: Short visual description for image generation (describe the action and visible elements, no quantities or timing)
```

### `server/app/services.py` — `RecipeStepModel` (line 26-29)

Add new fields:
```python
class RecipeStepModel(BaseModel):
    instruction: str
    duration: Optional[int] = None
    image_description: Optional[str] = None
    image_url: Optional[str] = None
```

No database migration needed — `recipes.steps` and `chat_sessions.recipe` are JSON columns. Adding new fields to the JSON objects is backward-compatible. Old recipes without these fields simply won't have images.

## Frontend

### `client/src/types/recipe.ts` — RecipeStep (line 10-13)

```typescript
export interface RecipeStep {
  instruction: string;
  duration?: number;
  image_description?: string;
  image_url?: string;
}
```

### `client/src/types/chat-message-types.ts` — Add new type and update union

Add after `RecipeNutritionUpdate` (around line 76):
```typescript
export type RecipeStepImageUpdate = {
  type: 'recipe_update';
  action: 'set_step_image';
  step_index: number;
  image_url: string;
};
```

Update the union type (line 78-82):
```typescript
export type RecipeUpdateContent =
  | RecipeMetadataUpdate
  | RecipeIngredientsUpdate
  | RecipeStepsUpdate
  | RecipeNutritionUpdate
  | RecipeStepImageUpdate;
```

### `client/src/hooks/useMealPlannerRecipe.ts` — Three changes

1. Add to `RecipeAction` union type (around line 15-32):
```typescript
| { type: 'SET_STEP_IMAGE'; payload: { step_index: number; image_url: string } }
```

2. Add reducer case in `recipeReducer` (inside the switch, around line 69-141):
```typescript
case 'SET_STEP_IMAGE': {
  const baseRecipe = state.recipe || createEmptyRecipe();
  const steps = [...(baseRecipe.steps || [])];
  if (steps[action.payload.step_index]) {
    steps[action.payload.step_index] = {
      ...steps[action.payload.step_index],
      image_url: action.payload.image_url,
    };
  }
  return { ...state, recipe: { ...baseRecipe, steps } };
}
```

3. Add case in `applyRecipeUpdate` switch (around line 153-198):
```typescript
case 'set_step_image':
  dispatch({
    type: 'SET_STEP_IMAGE',
    payload: { step_index: update.step_index, image_url: update.image_url },
  });
  break;
```

## Verification

- Generate a recipe and check the steps in the DB — each should now have `image_description`
- Check React devtools: recipe state should update when `set_step_image` messages arrive
- Save recipe, reload page — images persist

## Commit
```
feat: add image_description and image_url schema support across backend and frontend
```
