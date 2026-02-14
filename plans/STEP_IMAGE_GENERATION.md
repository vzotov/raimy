# Recipe Step Image Generation System — Master Plan

## Context

Raimy's recipe creator agent generates structured recipes (metadata, ingredients, steps, nutrition) but steps are text-only. This plan adds automated image generation for each recipe step, using a local GPU (FLUX.2 klein 4B) with fal.ai cloud fallback. A semantic cache (pgvector) avoids regenerating images for similar steps across all users.

The system introduces 3 new components: an image generation server (standalone, portable to remote GPU machine), an embedding microservice, and a GCS upload + cache orchestration pipeline in agent-service.

---

## Architecture Overview

```
Recipe Creator Agent (agent-service)
  generates steps with image_description field (LLM-produced)
  emits "complete" event
       |
Image Pipeline (agent-service/services/image_pipeline.py)
  FOR EACH STEP:
       |
  1. Use step.image_description (LLM-generated, cache-friendly)
  2. Get embedding -> POST embedding-service:8004/embed
  3. Query step_image_cache (pgvector cosine similarity)
       |
  +-- CACHE HIT -> return existing GCS URL
  +-- CACHE MISS:
       +-- Try local image-gen -> POST image-gen-service:8005/generate
       +-- Fallback -> fal.ai API
       |
  4. Upload PNG to GCS
  5. Insert into step_image_cache
  6. Publish "set_step_image" via Redis -> WebSocket -> Frontend
```

### Key Design: LLM-generated `image_description`

Instead of regex-based text normalization, the LLM generates an `image_description` field for each step during recipe creation. This is better because:

- **Context-aware**: The LLM knows when numbers matter ("combine flour, salt, and eggs") vs when they don't ("dice 2 onions")
- **Cache-friendly**: Produces canonical descriptions of the visual scene, improving cache hit rates
- **No fragile regex**: No risk of stripping semantically important content
- **Zero extra cost**: Generated alongside steps in the same LLM call

Examples:
- Step: "Dice 2 medium onions finely" -> `image_description`: "dicing onions finely on a cutting board"
- Step: "Combine 2 cups flour, 1 tsp salt, and 3 eggs in a bowl" -> `image_description`: "combining flour salt and eggs in a mixing bowl"
- Step: "Let the dough rest for 30 minutes covered" -> `image_description`: "dough resting covered with towel"

---

## Phases

Each phase has its own detailed implementation file in `plans/phases/`.

> **Requirement**: When implementing a phase, mark each checklist item as `[x]` in the phase file as it's completed. When the entire phase is done, also mark the Status column in the table below as `[x]`.

| Phase | Name | File | Status |
|-------|------|------|--------|
| 1 | Database — pgvector + step_image_cache | [phase-01-database.md](phases/phase-01-database.md) | [x] |
| 2 | Embedding Service | [phase-02-embedding-service.md](phases/phase-02-embedding-service.md) | [ ] |
| 3 | Image Generation Service (standalone) | [phase-03-image-gen-service.md](phases/phase-03-image-gen-service.md) | [x] |
| 4 | fal.ai Fallback Client | [phase-04-fal-client.md](phases/phase-04-fal-client.md) | [x] |
| 5 | GCS Storage Utility | [phase-05-gcs-storage.md](phases/phase-05-gcs-storage.md) | [x] |
| 6 | Image Orchestration Pipeline | [phase-06-image-pipeline.md](phases/phase-06-image-pipeline.md) | [x] |
| 7 | Trigger — Wire into Recipe Creator | [phase-07-trigger.md](phases/phase-07-trigger.md) | [x] |
| 8 | Redis + Backend Message Handling | [phase-08-redis-backend.md](phases/phase-08-redis-backend.md) | [x] |
| 9 | Schema Changes | [phase-09-schema-changes.md](phases/phase-09-schema-changes.md) | [x] |
| 10 | Frontend — Display Step Images | [phase-10-frontend.md](phases/phase-10-frontend.md) | [x] |

---

## Implementation Order

Phases 1-5 are independent. Recommended sequential order:

1. **Phase 1** (DB) -- foundation
2. **Phase 3** (Image Gen Service) -- standalone, test independently
3. **Phase 2** (Embedding Service) -- standalone, test independently
4. **Phase 4** (fal.ai client) -- single file
5. **Phase 5** (GCS storage) -- single file, requires one-time GCS bucket setup
6. **Phase 9** (Schema changes) -- type additions across backend + frontend
7. **Phase 6** (Pipeline) -- brings 1-5 together, the main integration
8. **Phase 7** (Trigger) -- small change in agent-service/main.py
9. **Phase 8** (Redis/Backend) -- small changes in redis_client + app/main.py
10. **Phase 10** (Frontend) -- display images in StepList

---

## Files Summary

### New files (12)

| File | Phase |
|------|-------|
| `server/alembic/versions/008_add_step_image_cache.py` | 1 |
| `server/app/models/step_image_cache.py` | 1 |
| `server/embedding-service/main.py` | 2 |
| `server/embedding-service/Dockerfile` | 2 |
| `server/embedding-service/requirements.txt` | 2 |
| `server/image-gen-service/main.py` | 3 |
| `server/image-gen-service/Dockerfile` | 3 |
| `server/image-gen-service/requirements.txt` | 3 |
| `server/agent-service/services/__init__.py` | 6 |
| `server/agent-service/services/image_pipeline.py` | 6 |
| `server/agent-service/services/fal_client.py` | 4 |
| `server/agent-service/services/gcs_storage.py` | 5 |

### Modified files (11)

| File | Phase | What changes |
|------|-------|-------------|
| `docker-compose.yml` | 1, 2, 4, 5, 7 | Postgres image -> pgvector, add embedding-service, add env vars + volume to agent-service |
| `.env.example` | 4, 5 | Add FAL_KEY, GCS_BUCKET_NAME |
| `server/requirements.txt` | 1 | Add pgvector |
| `server/app/models/__init__.py` | 1 | Import StepImageCache |
| `server/app/services.py` | 6, 8, 9 | Add 3 cache methods, update_step_image_url, RecipeStepModel fields |
| `server/agent-service/main.py` | 7 | Add import, _generate_step_images fn, modify "complete" case |
| `server/agent-service/requirements.txt` | 5 | Add google-cloud-storage |
| `server/agent-service/agents/recipe_creator/schemas.py` | 9 | Add image_description to Step |
| `server/agent-service/agents/recipe_creator/prompt.py` | 9 | Add image_description to GENERATE_STEPS_PROMPT |
| `server/core/redis_client.py` | 8 | Add send_step_image_message() |
| `server/app/main.py` | 8 | Add "set_step_image" case in handle_recipe_update_message |

### Frontend modified files (4)

| File | Phase |
|------|-------|
| `client/src/types/recipe.ts` | 9 |
| `client/src/types/chat-message-types.ts` | 9 |
| `client/src/hooks/useMealPlannerRecipe.ts` | 9 |
| `client/src/components/shared/StepList.tsx` | 10 |

---

## Environment Variables (new)

| Variable | Service | Description |
|----------|---------|-------------|
| `EMBEDDING_SERVICE_URL` | agent-service | Default: `http://embedding-service:8004` |
| `IMAGE_GEN_SERVICE_URL` | agent-service | Default: `http://host.docker.internal:8005` |
| `GCS_BUCKET_NAME` | agent-service | Default: `raimy-step-images` |
| `GOOGLE_APPLICATION_CREDENTIALS` | agent-service | Path to GCP service account JSON |
| `FAL_KEY` | agent-service | fal.ai API key |

---

## End-to-End Verification

1. Start all services: `docker compose up -d` + `cd server/image-gen-service && python main.py`
2. Open app, create new recipe-creator session
3. Ask for a recipe (e.g., "make me spaghetti carbonara")
4. Watch recipe card build: metadata -> ingredients -> steps -> nutrition
5. After "complete", step images should start appearing one by one (2-3s each)
6. Save recipe -> view saved recipe -> images persist
7. Ask for a similar recipe -> verify cache hits in logs
8. Stop image-gen-service -> generate another recipe -> verify fal.ai fallback works
