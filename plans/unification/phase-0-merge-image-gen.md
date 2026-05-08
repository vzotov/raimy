# Phase 0: Merge image-gen Branch

## Goal
Bring all image generation work into `dev` before any unified chat changes, so Phase 1+ builds on the latest codebase.

## What image-gen adds
- `ImageGenAgent` — generates FLUX-optimized prompts via LLM, produces step images stored in GCS
- `generate_images` intent in `KitchenAgent`
- Step image display in kitchen view (`StepList.tsx`)
- `SlidingPanelTrigger` component — toggle button for sliding panels
- `ConfirmDialog` component — Radix UI-based confirm dialogs (replaces `window.confirm`)
- `Dropdown` component — Radix UI-based dropdown menu
- `ThemeSelector` — refactored with new `Dropdown`
- Feature flag: `IMAGE_GEN_ENABLED` in `ConfigProvider` / `config.ts`
- gpt-5-chat-latest model upgrade in KitchenAgent

## Steps

```bash
git checkout dev
git merge image-gen
```

Likely conflict areas (both branches touch these files):
- `client/src/components/pages/kitchen/KitchenChat.tsx`
- `client/src/components/pages/recipe-creator/RecipeCreatorChat.tsx`
- `client/src/components/shared/chat/ChatMessages.tsx`
- `docker-compose.yml` (new image-gen service / env vars)
- `.env.example` (new FAL_API_KEY, GCS vars)

After resolving conflicts:
```bash
docker-compose up --build
cd client && npm install  # Radix UI packages added
npm run build             # Type-check and catch broken imports
```

## Smoke test
1. Create a kitchen session
2. Complete a recipe and start cooking
3. Trigger image generation — verify step images appear
4. Check `IMAGE_GEN_ENABLED` feature flag works (images hidden when flag off)

## Key new files
- `server/agent-service/agents/image_gen/agent.py` — `ImageGenAgent` class
- `server/agent-service/agents/image_gen/prompt.py` — `GENERATE_IMAGE_PROMPT`
- `server/agent-service/services/fal_client.py` — FAL.ai API client
- `server/agent-service/services/gcs_storage.py` — Google Cloud Storage upload
- `client/src/components/shared/SlidingPanelTrigger.tsx`
- `client/src/components/shared/ConfirmDialog.tsx`
- `client/src/components/shared/Dropdown.tsx`

## New env vars needed (add to `.env`)
```
FAL_API_KEY=...
GCS_BUCKET_NAME=...
GCS_PROJECT_ID=...
```
