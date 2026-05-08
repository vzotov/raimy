# Phase 2: New `/chat/[id]` Frontend with Dual-Mode UX

## Goal
Single route `/chat/[id]` with two visual modes — CHAT and COOK — that switch seamlessly based on conversation state.

## Mode Overview

**CHAT mode** (default)
- Standard chat interface (messages + input)
- Recipe panel (`SlidingPanel`) slides in from right when `recipe` is populated
- Agent sends `selector` message with actions; clicking an option sends it as a message

**COOK mode** (activates on first `kitchen-step` event)
- HelloFresh-style slide deck: one `CookingStep` card per screen
- Step image (top, full-width) + instruction text with bolded ingredients (bottom)
- Previous / Next navigation sends WebSocket messages
- Timer button appears inline when step has a timer
- "← Back to Chat" header button returns to CHAT mode (cooking state preserved)
- Chat overlay (slide-up drawer) for asking questions mid-cook

---

## New Files

```
client/src/app/chat/
  layout.tsx              — metadata (title template: "Chat | Raimy")
  page.tsx                — landing page redirects to /chat/new (or shows home chat input in Phase 3)
  new/page.tsx            — server component: POST session, redirect
  [id]/page.tsx           — server component: fetch session, Suspense → UnifiedContent

client/src/components/pages/chat/
  UnifiedContent.tsx      — server component: extract initial state, render UnifiedChat
  UnifiedChat.tsx         — 'use client': mode state, wires hook + WebSocket
  CookingView.tsx         — full-screen cooking slide deck container
  CookingStep.tsx         — single step card component

client/src/hooks/
  useUnifiedChatState.ts  — flat state hook for all chat + cooking + recipe state
```

---

## `app/chat/new/page.tsx`

Exact same pattern as `app/kitchen/new/page.tsx`:
```typescript
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export default async function NewChatSessionPage() {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();
  let sessionId: string | null = null;

  try {
    const response = await fetch(`${apiUrl}/api/chat-sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Cookie: cookieStore.toString() },
      body: JSON.stringify({ session_type: 'chat' }),
    });
    if (response.ok) {
      const data = await response.json();
      sessionId = data.session?.id ?? null;
    }
  } catch { /* fall through */ }

  redirect(sessionId ? `/chat/${sessionId}` : '/chat');
}
```

## `app/chat/[id]/page.tsx`

Same pattern as `app/kitchen/[id]/page.tsx`:
```typescript
export async function generateMetadata({ params }): Promise<Metadata> {
  const { id } = await params;
  const session = await fetchSession(id); // reuse existing server-side fetch helper
  return { title: session?.session_name || 'Chat' };
}

export default async function ChatSessionPage({ params }) {
  const { id } = await params;
  return (
    <Suspense fallback={<ChatSkeleton />}>
      <UnifiedContent id={id} />
    </Suspense>
  );
}
```

## `app/chat/layout.tsx`

```typescript
import type { Metadata } from 'next';
import { TITLE_TEMPLATE } from '@/constants/metadata';

export const metadata: Metadata = {
  title: { template: TITLE_TEMPLATE, default: 'Chat' },
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return children;
}
```

---

## `UnifiedContent.tsx` (server component)

Fetches session from API (with cookie auth), validates `session_type === 'chat'`, passes all initial state to `UnifiedChat`:

```typescript
interface UnifiedContentProps { id: string }

export default async function UnifiedContent({ id }: UnifiedContentProps) {
  const session = await fetchSessionWithMessages(id); // server-side with cookies()
  if (!session || session.session_type !== 'chat') notFound();

  return (
    <UnifiedChat
      sessionId={session.id}
      sessionName={session.session_name}
      initialMessages={session.messages || []}
      initialFinished={session.finished || false}
      initialRecipe={session.recipe ? { ...session.recipe, id: session.recipe_id || '' } : null}
      initialIsChanged={session.recipe_changed ?? false}
    />
  );
}
```

Note: No `initialIngredients` prop — ingredients are no longer tracked as separate state (they're inline in step text).

---

## `useUnifiedChatState.ts`

Flat hook, no composition of existing state hooks:

```typescript
import { useCallback, useReducer, useState } from 'react';
import { chatReducer } from '@/lib/messageHandlers/chatReducer';
import { useMealPlannerRecipe } from '@/hooks/useMealPlannerRecipe';
import { updateSessionNameInCache } from '@/hooks/useSessions';
import type { ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import type { SessionMessage } from '@/types/chat-session';
import type { Recipe } from '@/types/recipe';

interface Params {
  sessionId: string;
  initialMessages?: SessionMessage[];
  initialFinished?: boolean;
  initialRecipe?: Recipe | null;
  initialIsChanged?: boolean;
}

export function useUnifiedChatState({
  sessionId,
  initialMessages = [],
  initialFinished = false,
  initialRecipe = null,
  initialIsChanged = false,
}: Params) {
  // Messages: reducer needed for streaming (ADD_OR_UPDATE_MESSAGE by ID)
  const [messages, dispatch] = useReducer(chatReducer, convertInitialMessages(initialMessages));

  // Simple state
  const [agentStatus, setAgentStatus] = useState<string | null>(null);
  const [sessionName, setSessionName] = useState('');
  const [cookingComplete, setCookingComplete] = useState(initialFinished);
  const [cookingStarted, setCookingStarted] = useState(false);

  // Recipe state (reuse existing hook - it has applyRecipeUpdate, isRecipeChanged etc.)
  const { recipe, isRecipeChanged, applyRecipeUpdate, setRecipe, resetChangedFlag } =
    useMealPlannerRecipe(initialRecipe, initialIsChanged);

  const handleMessage = useCallback((wsMessage: WebSocketMessage) => {
    if (wsMessage.type === 'agent_message' && wsMessage.content) {
      const content = wsMessage.content;
      const messageId = wsMessage.message_id || `agent-${Date.now()}`;

      switch (content.type) {
        case 'recipe_update':
          applyRecipeUpdate(content);
          return;

        case 'cooking_complete':
          setCookingComplete(true);
          return;

        case 'kitchen-step':
          // First kitchen-step triggers mode switch
          // Note: content now includes timer_minutes and timer_label (added Phase 1)
          setCookingStarted(true);
          dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: buildMessage(content, messageId, 'assistant') });
          setAgentStatus(null);
          return;

        case 'recipe_saved':
          // Agent triggered save; update local recipe with returned ID
          if (recipe) setRecipe({ ...recipe, id: content.recipe_id });
          return;

        case 'session_name':
          setSessionName(content.name);
          updateSessionNameInCache(sessionId, content.name, 'chat');
          return;

        case 'text':
        case 'selector':
          dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: buildMessage(content, messageId, 'assistant') });
          setAgentStatus(null);
          return;

        default:
          dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: buildMessage(content, messageId, 'assistant') });
          setAgentStatus(null);
      }
    }

    if (wsMessage.type === 'system' && wsMessage.content) {
      const sys = wsMessage.content;
      if (sys.type === 'thinking') setAgentStatus(sys.message);
      else if (sys.type === 'connected') setAgentStatus(null);
      else if (sys.type === 'error') setAgentStatus(null);
    }
  }, [sessionId, applyRecipeUpdate]);

  const addMessage = useCallback((content: string) => {
    dispatch({
      type: 'ADD_OR_UPDATE_MESSAGE',
      payload: { id: `user-${Date.now()}`, role: 'user', content: { type: 'text', content }, timestamp: new Date() },
    });
    setAgentStatus('thinking');
  }, []);

  return {
    messages,
    agentStatus,
    sessionName,
    cookingComplete,
    cookingStarted,
    recipe,
    isRecipeChanged,
    handleMessage,
    addMessage,
    setRecipe,
    resetChangedFlag,
  };
}
```

**`updateSessionNameInCache`** — needs `'chat'` added to its session type union in `useSessions.ts` (see below).

---

## `UnifiedChat.tsx`

```typescript
'use client';

interface UnifiedChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
  initialFinished?: boolean;
  initialRecipe?: Recipe | null;
  initialIsChanged?: boolean;
}

export default function UnifiedChat({ sessionId, sessionName, ...initialProps }: UnifiedChatProps) {
  const state = useUnifiedChatState({ sessionId, ...initialProps });
  const [mode, setMode] = useState<'chat' | 'cook'>('chat');
  const [isChatOverlayOpen, setIsChatOverlayOpen] = useState(false);
  const [isRecipePanelOpen, setIsRecipePanelOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Transition to COOK mode when first kitchen-step received
  useEffect(() => {
    if (state.cookingStarted && mode === 'chat') setMode('cook');
  }, [state.cookingStarted]);

  // Auto-open recipe panel when recipe first appears
  useEffect(() => {
    if (state.recipe && mode === 'chat') setIsRecipePanelOpen(true);
  }, [!!state.recipe]);

  const { sendMessage, isConnected } = useWebSocket({
    sessionId,
    onMessage: state.handleMessage,
    autoReconnect: !state.cookingComplete,
  });

  const handleSendMessage = useCallback((content: string) => {
    state.addMessage(content);
    sendMessage(content);
  }, [state.addMessage, sendMessage]);

  const handleSaveRecipe = useCallback(async () => {
    if (!state.recipe) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      const response = await chatSessions.saveRecipe(sessionId);
      if (response.data?.recipe) state.setRecipe(response.data.recipe);
      state.resetChangedFlag();
    } catch {
      setSaveError('Failed to save recipe');
    } finally {
      setIsSaving(false);
    }
  }, [state.recipe, sessionId]);

  // Extract current step from messages (last kitchen-step message)
  const currentStep = useMemo(() => {
    const steps = state.messages.filter(m => m.content.type === 'kitchen-step');
    return steps.length > 0 ? steps[steps.length - 1].content : null;
  }, [state.messages]);

  if (state.cookingComplete) {
    return <CookingCompleteScreen onNewChat={() => router.push('/chat/new')} onMyRecipes={() => router.push('/myrecipes')} />;
  }

  if (mode === 'cook') {
    return (
      <CookingView
        currentStep={currentStep}
        allSteps={/* kitchen-step messages */}
        onNext={() => handleSendMessage('next step')}
        onPrev={() => handleSendMessage('previous step')}
        onBack={() => setMode('chat')}
        onOpenChat={() => setIsChatOverlayOpen(true)}
        agentStatus={state.agentStatus}
        // Chat overlay
        chatOverlayOpen={isChatOverlayOpen}
        onChatOverlayClose={() => setIsChatOverlayOpen(false)}
        messages={state.messages}
        onSendMessage={handleSendMessage}
        isConnected={isConnected}
      />
    );
  }

  // CHAT mode
  return (
    <div className="flex h-full w-full overflow-hidden">
      <div className="flex flex-1 flex-col min-w-0">
        <ChatHeader sessionName={state.sessionName || sessionName} isConnected={isConnected} />
        <Chat
          sessionId={sessionId}
          messages={state.messages}
          onSendMessage={handleSendMessage}
          isConnected={isConnected}
          agentStatus={state.agentStatus}
          placeholder="Ask me anything, or tell me what you'd like to cook..."
        />
      </div>

      {/* Recipe panel toggle button — only when recipe exists and panel closed */}
      {state.recipe && !isRecipePanelOpen && (
        <SlidingPanelTrigger
          onClick={() => setIsRecipePanelOpen(true)}
          hasChanges={state.isRecipeChanged}
        />
      )}

      {/* Recipe panel */}
      <SlidingPanel isOpen={isRecipePanelOpen} onClose={() => setIsRecipePanelOpen(false)}>
        <RecipeDocument
          recipe={state.recipe}
          onToggle={() => setIsRecipePanelOpen(false)}
          onSave={handleSaveRecipe}
          isSaving={isSaving}
          saveError={saveError}
          isRecipeChanged={state.isRecipeChanged}
          onClearError={() => setSaveError(null)}
        />
      </SlidingPanel>
    </div>
  );
}
```

---

## `CookingView.tsx` + `CookingStep.tsx`

### `CookingView.tsx` — container
Manages which step index is "current" from the array of `kitchen-step` messages received so far. Renders `CookingStep` for current index.

```typescript
interface CookingViewProps {
  currentStep: KitchenStepContent | null;
  allSteps: KitchenStepContent[];  // all kitchen-step messages received
  onNext: () => void;        // send "next step" message
  onPrev: () => void;        // send "previous step" message
  onBack: () => void;        // return to CHAT mode
  onOpenChat: () => void;    // open chat overlay
  agentStatus: string | null;
  // chat overlay props
  chatOverlayOpen: boolean;
  onChatOverlayClose: () => void;
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  isConnected: boolean;
}
```

Step index tracking: `useState` with `currentStepIndex`, incremented by `onNext`, decremented by `onPrev`. Display `allSteps[currentStepIndex]`.

Progress: `currentStepIndex + 1` of `allSteps.length` (note: total step count may come from recipe steps array).

### `CookingStep.tsx` — single step card

```
┌─────────────────────────────────────┐
│ ←  Step 2 of 6        [Chat button] │  header (h-14)
│ ● ● ○ ○ ○ ○  progress dots         │
├─────────────────────────────────────┤
│                                     │
│    [step image — aspect-video]      │  top half
│                                     │
├─────────────────────────────────────┤
│                                     │
│  Bring **4 cups of water** to boil  │  instruction text
│  in a large pot. Add **1 tbsp salt**.│  (markdown with bold)
│                                     │
│  ⏱ Set 8-min timer                  │  conditional timer button
│                                     │
│  [← Previous]         [Next Step →] │  navigation
└─────────────────────────────────────┘
```

Props:
```typescript
interface CookingStepProps {
  step: KitchenStepContent;    // includes timer_minutes, timer_label
  stepIndex: number;
  totalSteps: number;
  stepImage?: string;          // URL from image-gen step_image event
  onNext: () => void;
  onPrev: () => void;
  hasPrev: boolean;
  isLoading: boolean;          // agentStatus === 'thinking' while waiting for next step
}
```

- Instruction text rendered via existing markdown renderer (same `TextContent` component — bold already supported)
- Step image: `<img>` with `object-cover` inside `aspect-video` container (same pattern as image-gen branch's `StepList.tsx`)
- Timer button: shown when `step.timer_minutes` is present — reads directly from step content, no separate timer event or state

---

## `types/chat-message-types.ts` — add timer fields to `KitchenStepContent`

```typescript
// Before:
export type KitchenStepContent = {
  type: 'kitchen-step';
  message: string;
  next_step_prompt: string;
};

// After:
export type KitchenStepContent = {
  type: 'kitchen-step';
  message: string;
  next_step_prompt: string;
  timer_minutes?: number;   // ADD — set by UnifiedAgent step guidance
  timer_label?: string;     // ADD
};
```

Also add `recipe_saved` to the `MessageContent` union:
```typescript
export type RecipeSavedContent = {
  type: 'recipe_saved';
  recipe_id: string;
};

export type MessageContent = ... | RecipeSavedContent;
```

---

## `useSessions.ts` changes

```typescript
// Add 'chat' to the SWR key map
export const SESSIONS_KEYS = {
  recipeCreator: '/api/chat-sessions?type=recipe-creator',
  kitchen: '/api/chat-sessions?type=kitchen',
  chat: '/api/chat-sessions?type=chat',   // ADD
} as const;

// Add 'chat' to SessionType
type SessionType = 'recipe-creator' | 'kitchen' | 'chat';

// Add exported hook
export function useChatSessions() {
  return useSessions('chat');
}

// Update updateSessionNameInCache to handle 'chat'
export function updateSessionNameInCache(
  sessionId: string,
  sessionName: string,
  sessionType: 'recipe-creator' | 'kitchen' | 'chat',  // ADD 'chat'
) {
  const key =
    sessionType === 'kitchen' ? SESSIONS_KEYS.kitchen
    : sessionType === 'chat'  ? SESSIONS_KEYS.chat      // ADD
    : SESSIONS_KEYS.recipeCreator;
  // ... mutate
}
```

## `types/chat-session.ts` changes

```typescript
export interface ChatSession {
  // ...
  session_type: 'recipe-creator' | 'kitchen' | 'chat';  // ADD 'chat'
  // Remove: ingredients field (no longer tracked in state)
  recipe_changed?: boolean;  // ADD — needed by UnifiedContent
}
```

## `useChatState.ts` changes

Add `'chat'` to `sessionType` union (used in `handleSessionNameMessage` → `updateSessionNameInCache`):
```typescript
sessionType: 'recipe-creator' | 'kitchen' | 'chat';
```

---

## Reused components (no changes)
- `components/shared/chat/Chat.tsx` — chat messages + input
- `components/shared/chat/ChatMessages.tsx`
- `components/shared/chat/ChatInput.tsx`
- `components/shared/SlidingPanel.tsx`
- `components/shared/SlidingPanelTrigger.tsx` — from image-gen branch
- `components/shared/RecipeDocument.tsx`
- `lib/messageHandlers/chatReducer.ts`
- `hooks/useMealPlannerRecipe.ts`
- `hooks/useWebSocket.ts`

---

## Verification

1. `/chat/new` → POST `{session_type: 'chat'}` → redirect to `/chat/{id}` → greeting appears
2. Send "make tacos" → recipe_update events populate recipe panel → selector with Save/Cook/Buy
3. Click "Start Cooking" (selector option) → message sent → `kitchen-step` received → COOK mode activates
4. Step card shows image (if image-gen enabled) + instruction with bolded ingredients
5. Tap "Next Step →" → loading state → new step card appears
6. Tap timer button → timer set confirmation
7. Tap "← Back to Chat" → CHAT mode, recipe panel still present
8. Open chat in COOK mode overlay → type question → answer appears in overlay → close overlay → back at current step
9. Complete all steps → `cooking_complete` → completion screen
10. Old `/kitchen/*` routes → 404 (route doesn't exist)
