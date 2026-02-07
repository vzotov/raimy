'use client';

import classNames from 'classnames';
import { useRouter } from 'next/navigation';
import { useCallback } from 'react';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import NotebookIcon from '@/components/icons/NotebookIcon';
import KitchenIngredientList, {
  type KitchenIngredient,
} from '@/components/pages/kitchen/KitchenIngredientList';
import Chat from '@/components/shared/chat/Chat';
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
              <KitchenIngredientList ingredients={state.ingredients} />
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
