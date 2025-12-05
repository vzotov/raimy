'use client';

import classNames from 'classnames';
import { useCallback } from 'react';
import Chat from '@/components/shared/chat/Chat';
import IngredientList, {
  type Ingredient,
} from '@/components/shared/IngredientList';
import TimerList from '@/components/shared/TimerList';
import { useKitchenState } from '@/hooks/useKitchenState';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { SessionMessage } from '@/types/meal-planner-session';

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
    <div className="flex h-screen w-full">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-accent/20">
          <h1 className="text-2xl font-bold text-text">
            {state.sessionName || sessionName}
          </h1>
          <div className="flex items-center gap-4 mt-2">
            <p className="text-sm text-text/70">
              {state.messages.length} message
              {state.messages.length !== 1 ? 's' : ''}
            </p>
            <div className="flex items-center gap-2">
              <div
                className={classNames('w-2 h-2 rounded-full', {
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
            <p className="text-xs text-red-500 mt-1">
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

      {/* Sidebar with ingredients and timers */}
      <div className="w-80 border-l border-accent/20 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Ingredient List */}
          {state.ingredients.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-text mb-3">
                Ingredients
              </h2>
              <IngredientList ingredients={state.ingredients} />
            </div>
          )}

          {/* Timer List */}
          {state.timers.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-text mb-3">Timers</h2>
              <TimerList timers={state.timers} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
