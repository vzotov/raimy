'use client';

import classNames from 'classnames';
import { useCallback, useState } from 'react';
import Chat from '@/components/shared/chat/Chat';
import RecipeDocument from '@/components/shared/RecipeDocument';
import SlidingPanel from '@/components/shared/SlidingPanel';
import { useRecipeCreatorState } from '@/hooks/useRecipeCreatorState';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { RecipeContent } from '@/types/chat-message-types';
import type { SessionMessage } from '@/types/chat-session';

interface RecipeCreatorChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
  initialRecipe?: RecipeContent | null;
}

export default function RecipeCreatorChat({
  sessionId,
  sessionName,
  initialMessages = [],
  initialRecipe,
}: RecipeCreatorChatProps) {
  // Use composed state hook
  const { state, handleMessage, addMessage } = useRecipeCreatorState({
    sessionId,
    initialMessages,
    initialRecipe,
  });

  console.log('[RecipeCreatorChat] State:', initialRecipe);

  // UI-specific state (moved from hook)
  const [isRecipeVisible, setIsRecipeVisible] = useState(false);

  // WebSocket connection
  const { isConnected, error, sendMessage } = useWebSocket({
    sessionId,
    onMessage: handleMessage,
  });

  // Handle sending messages
  const handleSendMessage = useCallback(
    (content: string) => {
      addMessage(content);
      sendMessage(content);
    },
    [addMessage, sendMessage],
  );

  return (
    <div className="flex h-full w-full">
      {/* Main chat area */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col">
        {/* Header */}
        <div className="border-b border-accent/20 p-4">
          <h1 className="text-2xl font-bold text-text truncate">
            {state.sessionName || sessionName}
          </h1>
          <div className="mt-2 flex items-center gap-4">
            <p className="text-sm text-text/70">
              {state.messages.length} message
              {state.messages.length !== 1 ? 's' : ''}
            </p>
            <div className="flex items-center gap-2">
              <div
                className={classNames('h-2 w-2 rounded-full', {
                  'bg-green-500': isConnected,
                  'bg-yellow-500': !isConnected && !error,
                  'bg-red-500': error,
                })}
              />
              <span className="text-xs text-text/60">
                {error ? 'Error' : isConnected ? 'Connected' : 'Connecting...'}
              </span>
            </div>
          </div>
          {error && (
            <p className="mt-1 text-xs text-red-500">
              Connection error: {error}
            </p>
          )}
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <Chat
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            agentStatus={state.agentStatus}
            placeholder="Describe your meal preferences..."
          />
        </div>
      </div>

      {/* Tab button on right edge to open panel - only shown when panel is closed */}
      {!isRecipeVisible && state.recipe && (
        <button
          onClick={() => setIsRecipeVisible(true)}
          className="fixed top-[20%] right-0 z-30 md:hidden bg-primary text-white px-3 py-6 rounded-l-lg shadow-xl hover:bg-primary/90 transition-all"
          aria-label="Show recipe"
        >
          <div className="flex flex-col items-center gap-1">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <span className="text-xs font-medium">Recipe</span>
          </div>
        </button>
      )}

      {/* Recipe sidebar (desktop) / Expandable panel (mobile) */}
      <SlidingPanel
        isOpen={isRecipeVisible}
        onClose={() => setIsRecipeVisible(false)}
      >
        <RecipeDocument
          recipe={state.recipe}
          isVisible={true}
          onToggle={() => setIsRecipeVisible(false)}
        />
      </SlidingPanel>
    </div>
  );
}
