'use client';

import classNames from 'classnames';
import { useCallback } from 'react';
import Chat from '@/components/shared/chat/Chat';
import IngredientList, {
  type Ingredient,
} from '@/components/shared/IngredientList';
import { useKitchenState } from '@/hooks/useKitchenState';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { SessionMessage } from '@/types/chat-session';

interface KitchenChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
  initialIngredients?: Ingredient[];
}

export default function KitchenChat({
  sessionId,
  sessionName,
  initialMessages = [],
  initialIngredients = [],
}: KitchenChatProps) {
  // Use the custom hook for message handling and state management
  const { state, handleMessage, addMessage } = useKitchenState({
    sessionId,
    initialMessages,
    initialIngredients,
  });

  // WebSocket connection
  const { isConnected, error, sendMessage } = useWebSocket({
    sessionId,
    onMessage: handleMessage,
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

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <div className="border-b border-accent/20 p-4">
        <h1 className="truncate text-2xl font-bold text-text">
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
          <p className="mt-1 text-xs text-red-500">Connection error: {error}</p>
        )}
      </div>

      {/* Content area with ingredients and chat */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden md:flex-row">
        {/* Ingredients panel - stacked on mobile, sidebar on desktop */}
        {state.ingredients.length > 0 && (
          <div className="flex h-[32vh] w-full flex-shrink-0 flex-col md:order-last md:h-auto md:w-80 md:border-l md:border-accent/20">
            <div className="flex min-h-0 flex-1 flex-col pl-4 pt-4 pb-4 gap-4">
              <h2 className="flex-shrink-0 text-lg font-semibold text-text pr-4">
                Ingredients
              </h2>
              <IngredientList ingredients={state.ingredients} />
            </div>
          </div>
        )}

        {/* Chat */}
        <div className="min-h-0 flex-1 overflow-hidden">
          <Chat
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            agentStatus={state.agentStatus}
            placeholder="Ask about steps or ingredients..."
          />
        </div>
      </div>
    </div>
  );
}
