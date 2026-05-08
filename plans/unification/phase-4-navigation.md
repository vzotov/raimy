# Phase 4: Navigation & Session Menu

## Goal
Remove old Kitchen and Recipe Creator menu sections from the sidebar. Add a single "My Chats" section. The home page redesign is handled in Phase 3.

---

## `MainMenu.tsx` changes

Replace `KitchenMenuSection` and `RecipeCreatorMenuSection` with `ChatMenuSection`:

```typescript
// Before:
import KitchenMenuSection from '@/components/shared/menu/KitchenMenuSection';
import RecipeCreatorMenuSection from '@/components/shared/menu/RecipeCreatorMenuSection';
// ...
<KitchenMenuSection onMenuClose={onClose} />
<RecipeCreatorMenuSection onMenuClose={onClose} />

// After:
import ChatMenuSection from '@/components/shared/menu/ChatMenuSection';
// ...
<ChatMenuSection onMenuClose={onClose} />
```

Keep the "My Recipes" `Link` unchanged.

---

## New `ChatMenuSection.tsx`

Modeled exactly on `KitchenMenuSection.tsx` (88 lines). Same structure, different routes and hook:

```typescript
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useChatSessions } from '@/hooks/useSessions';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface ChatMenuSectionProps {
  onMenuClose: () => void;
}

export default function ChatMenuSection({ onMenuClose }: ChatMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  const { sessions, updateSessionName, deleteSession } = useChatSessions();

  useEffect(() => {
    if (pathname.startsWith('/chat')) setIsExpanded(true);
  }, [pathname]);

  const handleNewChat = () => {
    router.push('/chat/new');
    onMenuClose();
  };

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Delete this chat?')) return;
    try {
      await deleteSession(sessionId);
      if (pathname === `/chat/${sessionId}`) router.push('/');
    } catch { /* ignore */ }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/chat/${sessionId}`);
    onMenuClose();
  };

  return (
    <div>
      <SectionHeader
        title="My Chats"
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />
      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1">
          <button
            onClick={handleNewChat}
            className="w-full text-left px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
          >
            + New Chat
          </button>
          <SessionList
            sessions={sessions}
            currentPath={pathname}
            sessionType="chat"
            onUpdateSessionName={updateSessionName}
            onDelete={handleDelete}
            onSessionClick={handleSessionClick}
          />
        </div>
      )}
    </div>
  );
}
```

---

## `SessionList.tsx` changes

Add `'chat'` to the `sessionType` prop union. This prop is used on line 55 for the active check: `currentPath === '/${sessionType}/${session.id}'`.

```typescript
// Before:
sessionType: 'recipe-creator' | 'kitchen';
onSessionClick: (sessionId: string, sessionType: 'recipe-creator' | 'kitchen') => void;

// After:
sessionType: 'recipe-creator' | 'kitchen' | 'chat';
onSessionClick: (sessionId: string, sessionType: 'recipe-creator' | 'kitchen' | 'chat') => void;
```

---

## Delete old menu section files

```
client/src/components/shared/menu/KitchenMenuSection.tsx
client/src/components/shared/menu/RecipeCreatorMenuSection.tsx
```

---

## `app/chat/page.tsx`

The `/chat` landing page redirects to home (which now has the chat input):
```typescript
import { redirect } from 'next/navigation';
export default function ChatPage() {
  redirect('/');
}
```

---

## Verification

1. Sidebar: only "My Chats" section (no Kitchen, no Recipe Creator sections)
2. "+ New Chat" in sidebar → navigates to `/chat/new` → creates session
3. Clicking a session → navigates to `/chat/{id}` and section auto-expands
4. Deleting a session → session removed, redirects to `/` if currently on that session
5. "My Recipes" link in sidebar still works
