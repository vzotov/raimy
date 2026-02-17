'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import NotebookIcon from '@/components/icons/NotebookIcon';
import KitchenIngredientList, {
  type KitchenIngredient,
} from '@/components/pages/kitchen/KitchenIngredientList';
import Chat from '@/components/shared/chat/Chat';
import { ChatHeader } from '@/components/shared/ChatHeader';
import SlidingPanel from '@/components/shared/SlidingPanel';
import SlidingPanelTrigger from '@/components/shared/SlidingPanelTrigger';
import { useChatSessionTitle } from '@/hooks/useChatSessionTitle';
import { useKitchenState } from '@/hooks/useKitchenState';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { SessionMessage } from '@/types/chat-session';

interface KitchenChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
  initialIngredients?: KitchenIngredient[];
  initialFinished?: boolean;
}

export default function KitchenChat({
  sessionId,
  sessionName,
  initialMessages = [],
  initialIngredients = [],
  initialFinished = false,
}: KitchenChatProps) {
  const router = useRouter();

  // Use the custom hook for message handling and state management
  const { state, handleMessage, addMessage } = useKitchenState({
    sessionId,
    initialMessages,
    initialIngredients,
    initialFinished,
  });

  // Update document title when session name changes via WebSocket
  useChatSessionTitle(state.sessionName);

  // WebSocket connection - only connect if session not finished
  const { isConnected, error, sendMessage } = useWebSocket({
    sessionId,
    onMessage: handleMessage,
    autoReconnect: !state.cookingComplete,
  });

  // Handle sending messages
  const handleSendMessage = useCallback(
    (content: string) => {
      // Add user message optimistically
      addMessage(content);

      // Send via WebSocket
      sendMessage(content);
    },
    [addMessage, sendMessage],
  );

  const [isIngredientsVisible, setIsIngredientsVisible] = useState(false);

  // Show completion UI if cooking is complete
  if (state.cookingComplete) {
    // Get the last assistant message as the final message
    const lastAssistantMessage = [...state.messages]
      .reverse()
      .find((m) => m.role === 'assistant');
    const finalMessage =
      typeof lastAssistantMessage?.content === 'string'
        ? lastAssistantMessage.content
        : typeof lastAssistantMessage?.content === 'object' &&
            'content' in lastAssistantMessage.content
          ? lastAssistantMessage.content.content
          : typeof lastAssistantMessage?.content === 'object' &&
              'message' in lastAssistantMessage.content
            ? lastAssistantMessage.content.message
            : null;

    return (
      <div className="flex h-full w-full flex-col items-center justify-center p-8">
        <div className="max-w-lg text-center">
          <div className="mb-4 text-6xl">🎉</div>
          <h1 className="mb-4 text-3xl font-bold text-text">
            {state.sessionName || sessionName}
          </h1>
          {finalMessage && (
            <p className="text-lg text-text/80">{finalMessage}</p>
          )}
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => router.push('/kitchen/new')}
              className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-white transition-colors hover:bg-primary/90"
            >
              <ChefHatIcon className="h-5 w-5" />
              Cook Something New
            </button>
            <button
              onClick={() => router.push('/myrecipes')}
              className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-text/10 bg-surface px-6 py-3 font-medium text-text transition-colors hover:bg-surface/70"
            >
              <NotebookIcon className="h-5 w-5" />
              Browse My Recipes
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col">
        <ChatHeader
          title={state.sessionName || sessionName}
          isConnected={isConnected}
          error={error}
        />

        <div className="flex-1 overflow-hidden">
          <Chat
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            agentStatus={state.agentStatus}
            placeholder="Ask about steps or ingredients..."
          />
        </div>
      </div>

      {!isIngredientsVisible && state.ingredients.length > 0 && (
        <SlidingPanelTrigger
          onClick={() => setIsIngredientsVisible(true)}
          icon={
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <circle cx="5" cy="6" r="1.5" />
              <rect x="9" y="5" width="11" height="2" rx="1" />
              <circle cx="5" cy="12" r="1.5" />
              <rect x="9" y="11" width="11" height="2" rx="1" />
              <circle cx="5" cy="18" r="1.5" />
              <rect x="9" y="17" width="11" height="2" rx="1" />
            </svg>
          }
          label="Ingredients"
        />
      )}

      {state.ingredients.length > 0 && (
        <SlidingPanel
          isOpen={isIngredientsVisible}
          onClose={() => setIsIngredientsVisible(false)}
        >
          <div className="flex min-h-0 flex-1 flex-col p-4 gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-text">Ingredients</h2>
              <button
                onClick={() => setIsIngredientsVisible(false)}
                className="md:hidden p-2 hover:bg-accent/10 rounded text-text/60 hover:text-text"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <KitchenIngredientList ingredients={state.ingredients} />
          </div>
        </SlidingPanel>
      )}
    </div>
  );
}
