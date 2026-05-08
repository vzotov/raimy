# Phase 5: Delete Old Routes and Agents

## Goal
Remove all dead code. Run only after Phases 1–4 are stable and verified in production.

## Pre-conditions
- Phases 1–4 deployed and verified
- All users on unified chat routes
- No traffic to old routes (check access logs or analytics)

---

## Frontend Deletions

### App routes (entire directories)
```
client/src/app/kitchen/
client/src/app/recipe-creator/
```

### Page components (entire directories)
```
client/src/components/pages/kitchen/
client/src/components/pages/recipe-creator/
```
This removes: `KitchenChat.tsx`, `KitchenChatSkeleton.tsx`, `KitchenContent.tsx`, `KitchenIngredientList.tsx`, `RecipeCreatorChat.tsx`, `RecipeCreatorContent.tsx`, etc.

### Hooks
```
client/src/hooks/useKitchenState.ts
client/src/hooks/useRecipeCreatorState.ts
```

### Menu sections (already deleted in Phase 4, confirm)
```
client/src/components/shared/menu/KitchenMenuSection.tsx
client/src/components/shared/menu/RecipeCreatorMenuSection.tsx
```

### `useSessions.ts` cleanup
Remove dead exports:
```typescript
// Remove:
export function useKitchenSessions() { ... }
export function useRecipeCreatorSessions() { ... }

// Remove from SESSIONS_KEYS:
recipeCreator: '/api/chat-sessions?type=recipe-creator',
kitchen: '/api/chat-sessions?type=kitchen',

// Narrow SessionType:
type SessionType = 'chat';   // was: 'recipe-creator' | 'kitchen' | 'chat'
```

### `useChatState.ts` cleanup
Remove old types from `sessionType` union — now only `'chat'`.

### `types/chat-session.ts` cleanup
```typescript
// Narrow session_type:
session_type: 'chat';  // was: 'recipe-creator' | 'kitchen' | 'chat'
```

---

## Backend Deletions

### `server/agent-service/agents/kitchen/`
Delete entire directory — `KitchenAgent` is no longer used from registry.

**Check first**: ensure `UnifiedAgent` does not import from `kitchen/` — it imports `RecipeCreatorAgent` and `ImageGenAgent` only.

### `server/agent-service/agents/recipe_creator/`
**Keep** if `RecipeCreatorAgent` is still used as internal tool by `UnifiedAgent`. If `UnifiedAgent` has fully inlined its recipe creation logic by this point, delete.

### `server/agent-service/agents/registry.py` final state
Should already be clean from Phase 1. Verify no dead imports remain.

### `server/agent-service/main.py` final state
Verify no remaining `isinstance(agent, KitchenAgent)` or `isinstance(agent, RecipeCreatorAgent)` branches. Confirm `_handle_recipe_creator_events` is gone.

### `server/app/main.py` final state
Remove any remaining `session_type == "recipe-creator"` or `session_type == "kitchen"` conditionals.

---

## Database note
Old `kitchen` and `recipe-creator` session rows remain in the DB — no migration needed. They're simply not surfaced in UI. If a cleanup is desired later, a one-off script can delete them, but that's out of scope.

---

## Verification

```bash
# Type check
cd client && npx tsc --noEmit

# Build
npm run build

# Backend services start cleanly
docker-compose up --build

# No broken imports
grep -r "KitchenMenuSection\|RecipeCreatorMenuSection\|useKitchenState\|useRecipeCreatorState" client/src/
# Expect: no results

grep -r "KitchenAgent\|RecipeCreatorAgent" server/agent-service/agents/registry.py
# Expect: no results (or only in unified/agent.py if RecipeCreatorAgent kept as tool)
```

Old routes return 404:
- `GET /kitchen` → 404
- `GET /kitchen/new` → 404
- `GET /recipe-creator` → 404
