# Architecture Reference

Quick reference for every meaningful file in the codebase. Start here before exploring.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 + React 19 + TypeScript + TailwindCSS 4, hosted on Vercel |
| Backend | FastAPI (Python 3.11), 3 active services via Docker Compose |
| AI | LangGraph + LangChain, OpenAI models |
| Database | PostgreSQL 15 with pgvector, SQLAlchemy async + Alembic migrations |
| Messaging | Redis pub/sub for inter-service events and WebSocket routing |
| Reverse proxy | Caddy (automatic HTTPS via Let's Encrypt) |

---

## Directory Map

```
raimy/
├── client/                  Next.js frontend
├── server/                  Python backend services
│   ├── app/                 Main API service (port 8000)
│   ├── agent-service/       LangGraph agent service (port 8003)
│   ├── auth-service/        Google OAuth + JWT (port 8001)
│   ├── core/                Shared utilities (Redis, auth client)
│   ├── alembic/             Database migrations
│   └── (disabled)           image-gen-service, video-gen-service, embedding-service
├── deploy/                  GCP deployment scripts
├── docs/                    Project documentation
├── plans/                   Claude Code implementation plans
├── docker-compose.yml       Local development
├── docker-compose.prod.yml  Production
├── Caddyfile                Reverse proxy config
└── .env / .env.prod         Environment variables
```

---

## Backend Services

| Service | Port | Entry point | Purpose |
|---------|------|-------------|---------|
| raimy-api | 8000 | `server/app/main.py` | Main API, WebSocket connections, DB writes |
| agent-service | 8003 | `server/agent-service/main.py` | LangGraph agents, AI processing |
| auth-service | 8001 | `server/auth-service/main.py` | Google OAuth 2.0 + JWT token management |

Disabled (not running): `image-gen-service`, `video-gen-service`, `embedding-service`

---

## server/app/ — Main API

### Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `routes/chat_sessions.py` | `GET/POST /api/chat-sessions`, `WS /ws/{session_id}`, `POST /api/chat-sessions/{id}/save-recipe`, `POST /api/chat-sessions/{id}/steps/{idx}/generate-image` | Chat session CRUD, WebSocket streaming, save recipe from session |
| `routes/recipes.py` | `GET/POST/DELETE /api/recipes`, `GET /api/recipes/{id}`, `POST /api/recipes/{id}/instacart-link` | Recipe CRUD, Instacart shopping link generation |
| `routes/user.py` | `GET/PUT /api/user/profile`, `GET/DELETE /api/user/memory` | User profile, language preference, wipe memory |
| `routes/auth_proxy.py` | `POST /api/auth/*` | Proxies auth requests to auth-service |
| `routes/timers.py` | `GET/POST /api/timers` | Cooking timer management |
| `routes/config.py` | `GET /api/config` | Feature flags and app configuration |

### Models (SQLAlchemy)

| File | Table | Key columns |
|------|-------|-------------|
| `models/recipe.py` | `recipes` | id, name, description, ingredients (JSON), steps (JSON), nutrition (JSON), tags (Array), user_id, chat_session_id, instacart_link_url |
| `models/chat_session.py` | `chat_sessions` | id, type (recipe-creator/kitchen), name, recipe (JSON), recipe_id, agent_state (JSON), user_id |
| `models/chat_message.py` | `chat_messages` | id, session_id, role, content (JSON), created_at |
| `models/user.py` | `users` | email (PK), name, picture, language |
| `models/user_memory.py` | `user_memories` | id, user_id, content, created_at |
| `models/step_image_cache.py` | `step_image_cache` | id, description, image_url, embedding |
| `models/session.py` | `sessions` | id, user_id, expires_at (legacy auth sessions) |
| `models/base.py` | — | TimestampMixin (created_at, updated_at) |

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app init, ConnectionManager (WebSocket), router registration, auto-migrations |
| `services.py` | DB service layer + Pydantic API models: `RecipeIngredientModel` (name, amount, unit, notes, eng_name, group), `RecipeStepModel` (instruction, duration, image_description, image_url, group), `RecipeModel` |
| `database.py` | SQLAlchemy async engine + `AsyncSessionLocal` factory |

---

## server/agent-service/ — Agent Service

See [agents.md](agents.md) for full agent system documentation.

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, `POST /agent/chat` endpoint, Redis event streaming to WebSocket |
| `agents/base.py` | `BaseAgent` abstract class, `AgentEvent` dataclass |
| `agents/unified/` | Main orchestrator agent — see agents.md |
| `agents/recipe_creator/` | Recipe generation agent — see agents.md |
| `agents/memory/` | User memory extraction — see agents.md |
| `agents/image_gen/` | Step image generation — see agents.md |
| `services/fal_client.py` | FAL.ai image generation API client |
| `services/gcs_storage.py` | Google Cloud Storage client for image persistence |

---

## server/auth-service/ — Auth Service

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app on port 8001 |
| `auth.py` | `GET /auth/google` (OAuth redirect), `GET /auth/google/callback`, `POST /auth/verify`, `POST /auth/refresh`, `POST /auth/logout` |

---

## server/core/ — Shared Utilities

| File | Purpose |
|------|---------|
| `redis_client.py` | Redis connection factory, pub/sub helpers, `send_recipe_*_message()` helpers |
| `auth_client.py` | HTTP client for verifying JWT tokens against auth-service |

---

## server/alembic/versions/ — Migrations

| Migration | Changes |
|-----------|---------|
| 001 | Initial schema: users, recipes, sessions |
| 002 | chat_sessions table (type, name, recipe JSON, agent_state) |
| 003 | instacart_link_url cache column on recipes |
| 004 | nutrition JSON column on recipes |
| 005 | agent_state JSON column on chat_sessions |
| 006 | Enlarged picture URL column on users |
| 007 | user_memories table |
| 008 | step_image_cache table with embedding column |

---

## client/ — Frontend

### Pages (Next.js App Router — `client/src/app/`)

| Route | File | Purpose |
|-------|------|---------|
| `/` | `page.tsx` | Home page with navigation cards |
| `/chat` | `chat/page.tsx` | Session list |
| `/chat/new` | `chat/new/page.tsx` | Create new session |
| `/chat/[id]` | `chat/[id]/page.tsx` | Active chat / cooking session |
| `/recipe/[id]` | `recipe/[id]/page.tsx` | Recipe detail view |
| `/myrecipes` | `myrecipes/page.tsx` | Saved recipe library |
| `/profile` | `profile/page.tsx` | User profile and settings |
| `/auth/google` | `auth/google/route.ts` | Initiates Google OAuth |
| `/auth/google/callback` | `auth/google/callback/route.ts` | OAuth callback handler |
| `/auth/logout` | `auth/logout/route.ts` | Logout endpoint |
| `/auth/me` | `auth/me/route.ts` | Current user endpoint |

### Page Components (`client/src/components/pages/`)

| Component | Purpose |
|-----------|---------|
| `chat/UnifiedContent.tsx` | Chat page container, session type routing |
| `chat/UnifiedChat.tsx` | Chat UI: message list + input, WebSocket integration |
| `chat/CookingCompleteScreen.tsx` | Success screen after finishing a recipe |
| `home/HomeContent.tsx` | Home page content |
| `home/HomePageNavCard.tsx` | Navigation card (Chat / Recipes / Profile) |
| `recipe/RecipeContent.tsx` | Server component, fetches recipe + renders RecipeDetail |
| `myrecipes/RecipeList.tsx` | Recipe library grid |
| `profile/ProfileContent.tsx` | Profile form (name, language preference) |
| `profile/LanguageSelector.tsx` | Language preference dropdown |
| `profile/WipeMemoryButton.tsx` | Clears user memory |
| `profile/SignOutButton.tsx` | Logout button |

### Shared Components (`client/src/components/shared/`)

| Component | Purpose |
|-----------|---------|
| `Chat.tsx` | Core chat container |
| `ChatInput.tsx` | Message input field |
| `ChatMessage.tsx` | Single message bubble |
| `ChatMessages.tsx` | Scrollable message list with auto-scroll |
| `ThinkingIndicator.tsx` | AI thinking spinner |
| `chat/message-types/MessageRenderer.tsx` | Dispatches message content to type-specific renderer |
| `chat/message-types/MessageSelectorButtons.tsx` | Clickable option buttons |
| `chat/message-types/MessageConfirmationButtons.tsx` | Yes/No/Confirm buttons |
| `RecipeDetail.tsx` | Full recipe display (ingredients, steps, nutrition, actions) |
| `RecipeDocument.tsx` | Print-friendly recipe layout |
| `RecipeCard.tsx` | Recipe preview card for library grid |
| `IngredientList.tsx` | Renders ingredients; supports grouped sections (group field) |
| `StepList.tsx` | Renders steps with numbered badges; supports grouped sections; passes flat index to onGenerateImage |
| `NutritionSection.tsx` | Nutrition facts display |
| `InstacartButton.tsx` | Triggers Instacart shopping link |
| `TimerList.tsx` | Active cooking timers |
| `SectionTitle.tsx` | Sticky section header (Ingredients / Instructions / Nutrition) |
| `MainMenu.tsx` | Left navigation sidebar |
| `ChatHeader.tsx` | Top bar in chat view |
| `menu/SessionList.tsx` | List of chat sessions in sidebar |
| `menu/SessionItem.tsx` | Single session row (edit + display modes) |

### Hooks (`client/src/hooks/`)

| Hook | State managed |
|------|--------------|
| `useAuth.ts` | Current user, login state, session token |
| `useWebSocket.ts` | WS connection to `/ws/{sessionId}`, message receiving, reconnect |
| `useUnifiedChatState.ts` | All chat UI state: messages, input, recipe, timers, session type, agent status |
| `useMealPlannerRecipe.ts` | Recipe data binding — merges WS recipe events into local recipe state |
| `useSessions.ts` | Session list, create/delete/rename |
| `useChatMessages.ts` | Message history fetch + pagination |
| `useChatSessionTitle.ts` | Session name updates from agent |

### Types (`client/src/types/`)

| File | Key types |
|------|-----------|
| `recipe.ts` | `Recipe`, `RecipeIngredient` (name, amount, unit, notes, group), `RecipeStep` (instruction, duration, image_url, group), `RecipeNutrition` |
| `chat-message-types.ts` | `MessageContent` union — all message payload shapes |
| `chat-session.ts` | `ChatSession`, `SessionType` (`chat` \| `recipe-creator` \| `kitchen`) — `chat` is current, others legacy |
| `auth.ts` | `User`, `AuthContext` |
| `ingredient.ts` | `BaseIngredient` |
| `config.ts` | `AppConfig`, feature flags |

### Utilities (`client/src/lib/`)

| File | Purpose |
|------|---------|
| `api.ts` | HTTP client wrapper — `get/post/put/del` with auth headers and error handling |
| `serverAuth.ts` | Server-side JWT verification for Next.js route handlers |
| `messageHandlers/chatReducer.ts` | Reducer handling all incoming WS message types |
| `messageHandlers/textHandler.ts` | Handles `text` message type |
| `messageHandlers/systemHandler.ts` | Handles system/status messages |
| `messageHandlers/sessionNameHandler.ts` | Handles `session_name` updates |

---

## Data Flows

### Chat / WebSocket
Client opens WS to `/ws/{session_id}`. `ConnectionManager` in `main.py` authenticates at connection time and subscribes to a Redis channel keyed by session_id. When the user sends a message, the API POSTs to `agent-service/agent/chat`. The agent service processes the request, publishing events to Redis as they stream. `main.py` reads from Redis and forwards each event over the WebSocket. The frontend `useWebSocket` hook receives events and routes them through `chatReducer` to update UI state.

### Recipe Creation
When session type is `recipe-creator`, the `UnifiedAgent` delegates to `RecipeCreatorAgent`. The recipe_creator runs a LangGraph sequential workflow, yielding events: `thinking` → `session_name` → `metadata` → `ingredients` → `steps` → `nutrition` → `selector`. The unified agent intercepts each event, accumulates recipe data, suppresses the final `selector` from recipe_creator, and after `recipe_created` emits its own `selector` offering "Start cooking" or "Explore recipe". The user saves via `POST /api/chat-sessions/{id}/save-recipe`.

### Kitchen Session
When session type is `kitchen`, `UnifiedAgent` runs in kitchen mode. It emits `kitchen_step` events containing guidance for the current step along with `next_step_prompt`. `agent_state` events carry `current_step` index, stored in `chat_sessions.agent_state`. When all steps are done it emits `cooking_complete`.

### Image Generation
Agent emits `generate_images` event. Frontend calls `POST /api/chat-sessions/{id}/steps/{step_index}/generate-image`. API calls agent-service `/agent/generate-step-image`. Agent-service uses `fal_client.py` to generate an image via FAL.ai, uploads to GCS via `gcs_storage.py`, caches the URL in `step_image_cache`, and returns `image_url`. The step's `image_url` is updated in the session recipe JSON.

### User Memory
After each recipe save, `MemoryAgent` is triggered asynchronously. It reads the conversation, extracts dietary preferences, skill level, and cuisine preferences, and stores them in `user_memories`. On subsequent sessions, the agent service loads the user's memories and injects them into the agent's context at the start of each prompt.

---

## Infrastructure

### Docker Compose (local dev)

| Service | Image | Purpose |
|---------|-------|---------|
| raimy-api | local Dockerfile | Main API |
| agent-service | server/agent-service/Dockerfile | Agent service |
| auth-service | server/auth-service/Dockerfile | Auth service |
| postgres | pgvector/pgvector:pg15 (dev) / postgres:15-alpine (prod) | Database; dev image includes pgvector extension |
| redis | redis:7-alpine | Pub/sub + session cache |
| pgadmin | dpage/pgadmin4 | DB admin UI (port 8080) |

### Caddyfile Routing

| Path | Target |
|------|--------|
| `/auth/*` | auth-service:8001 |
| `/api/*` | raimy-api:8000 |
| `/ws/*` | raimy-api:8000 (with WebSocket headers) |
| `/health` | raimy-api:8000 |

### Deploy Scripts

| Script | Purpose |
|--------|---------|
| `deploy/deploy-from-github.sh` | Primary release: pulls branch from GitHub on VM, rebuilds, restarts |
| `deploy/gcp-vm-deploy.sh` | VM lifecycle: create / update / ssh / logs / ip / destroy |
| `deploy/setup-vm.sh` | One-time VM setup (Docker install, etc.) |

---

## Key Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API access |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth secret |
| `SERVICE_API_KEY` | Yes | Inter-service authentication token |
| `JWT_SECRET` | Yes | JWT signing key |
| `POSTGRES_DB/USER/PASSWORD` | Yes | Database credentials |
| `REDIS_URL` | Yes | Redis connection string |
| `DATABASE_URL` | Yes | Async PostgreSQL connection string |
| `API_DOMAIN` | Prod | Backend domain for Caddy + CORS |
| `FRONTEND_DOMAIN` | Prod | Frontend domain for CORS |
| `LETSENCRYPT_EMAIL` | Prod | Certificate notification email |
| `AUTO_MIGRATE` | Prod | Run Alembic on startup (default true) |
| `IMAGE_GEN_ENABLED` | Optional | Enable FAL.ai image generation |
| `INSTACART_API_KEY` | Optional | Instacart shopping link integration |
| `LANGCHAIN_TRACING_V2` | Optional | LangSmith tracing for debugging |
