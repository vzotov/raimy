'use client';

import classNames from 'classnames';
import { useCallback, useState } from 'react';
import Chat from '@/components/shared/chat/Chat';
import RecipeDocument from '@/components/shared/RecipeDocument';
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
    <div className="flex h-screen w-full">
      {/* Main chat area */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col">
        {/* Header */}
        <div className="border-b border-accent/20 p-4">
          <h1 className="text-2xl font-bold text-text">
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
          />
        </div>
      </div>

      {/* Recipe sidebar (desktop) / Expandable panel (mobile) */}
      <div className="w-full border-l border-accent/20 md:w-96">
        <RecipeDocument
          recipe={state.recipe}
          isVisible={isRecipeVisible}
          onToggle={() => setIsRecipeVisible(!isRecipeVisible)}
        />
      </div>
    </div>
  );
}
