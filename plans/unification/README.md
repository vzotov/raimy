# Unified Chat Experience — Master Plan

## Vision
Replace the two-chat architecture (recipe-creator / kitchen) with a single seamless chat experience. One conversation handles everything: recipe Q&A, recipe creation, step-by-step cooking guidance. The UI adapts to context — recipe panel when creating, HelloFresh-style slide deck when cooking.

## Phases

| Phase | Scope | Status |
|-------|-------|--------|
| [Phase 0](./phase-0-merge-image-gen.md) | Merge image-gen branch | TODO |
| [Phase 1](./phase-1-unified-agent.md) | New UnifiedAgent backend | TODO |
| [Phase 2](./phase-2-unified-frontend.md) | New `/chat/[id]` frontend with dual-mode UX | TODO |
| [Phase 3](./phase-3-home-page.md) | Home page: welcome input + LLM-generated suggestions | TODO |
| [Phase 4](./phase-4-navigation.md) | Sidebar navigation & session menu | TODO |
| [Phase 5](./phase-5-cleanup.md) | Delete old routes and agents | TODO |

## Key Decisions

- **No backward compatibility** — no customers yet; old sessions stay in DB as archive
- **Single session type**: `"chat"` — remove all `session_type` branching
- **Reuse agents as tools**: `RecipeCreatorAgent` and `ImageGenAgent` stay as internal tools inside `UnifiedAgent`
- **Proactive UX**: After recipe creation, agent offers Save / Start Cooking / Buy Ingredients via `selector` message
- **COOK mode**: HelloFresh-style slide deck — step image + instruction with inline bolded ingredients (no separate ingredient list)
- **Home page**: chat input directly on landing page — typing and sending creates a new session
- **State**: `useReducer` for messages (streaming updates), plain `useState` for everything else
