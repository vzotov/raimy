'use client';

import { useState, useCallback } from 'react';
import { useWebSocket, ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import Chat from '@/components/shared/chat/Chat';
import { ChatMessage } from '@/hooks/useChatMessages';
import { SessionMessage } from '@/types/meal-planner-session';
import {
  MessageContent,
  RecipeNameContent,
  IngredientsContent,
  TimerContent
} from '@/types/chat-message-types';
import IngredientList, { Ingredient } from '@/components/shared/IngredientList';
import TimerList, { Timer } from '@/components/shared/TimerList';
import classNames from 'classnames';

interface KitchenChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
}

export default function KitchenChat({
  sessionId,
  sessionName,
  initialMessages = [],
}: KitchenChatProps) {
  // Convert initial messages to ChatMessage format
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    initialMessages.map((msg, index) => ({
      id: `msg-${index}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp: new Date(msg.created_at),
    }))
  );

  // Kitchen-specific state
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [timers, setTimers] = useState<Timer[]>([]);
  const [recipeName, setRecipeName] = useState<string>('');
  const [agentStatus, setAgentStatus] = useState<string | null>(null);

  // Memoize WebSocket callbacks to prevent reconnections
  const handleMessage = useCallback((wsMessage: WebSocketMessage) => {
    console.log('[KitchenChat] Received:', wsMessage);

    // Handle agent messages - route by content type
    if (wsMessage.type === 'agent_message' && wsMessage.content) {
      const content = wsMessage.content;

      // Route based on content type (application layer)
      switch (content.type) {
        case 'text':
        case 'recipe':
          // Add to chat history
          const newMessage: ChatMessage = {
            id: wsMessage.message_id || `agent-${Date.now()}`,
            role: 'assistant',
            content: content as MessageContent,
            timestamp: new Date(),
          };
          // Clear agent status when we receive agent response
          setAgentStatus(null);
          setMessages((prev) => [...prev, newMessage]);
          break;

        case 'recipe_name':
          // Update recipe name state
          const recipeNameContent = content as RecipeNameContent;
          if (recipeNameContent.name) {
            setRecipeName(recipeNameContent.name);
          }
          break;

        case 'ingredients':
          // Update ingredients state
          const ingredientsContent = content as IngredientsContent;
          if (ingredientsContent.action === 'set' && ingredientsContent.items) {
            setIngredients(ingredientsContent.items);
          } else if (ingredientsContent.action === 'update' && ingredientsContent.items) {
            setIngredients((prev) =>
              prev.map((ing) => {
                const update = ingredientsContent.items?.find((u) => u.name === ing.name);
                return update ? { ...ing, ...update } : ing;
              })
            );
          }
          break;

        case 'timer':
          // Add timer to state
          const timerContent = content as TimerContent;
          if (timerContent.duration && timerContent.label) {
            const newTimer: Timer = {
              id: `timer-${Date.now()}`,
              duration: timerContent.duration,
              label: timerContent.label,
              startedAt: timerContent.started_at || Date.now() / 1000,
            };
            setTimers((prev) => [...prev, newTimer]);
          }
          break;
      }
    }

    // Handle system messages
    if (wsMessage.type === 'system' && wsMessage.content) {
      const systemContent = wsMessage.content;

      switch (systemContent.type) {
        case 'connected':
          console.log('✅', systemContent.message);
          break;

        case 'thinking':
          // Set agent status to show thinking indicator
          setAgentStatus(systemContent.message);
          break;

        case 'error':
          console.error('❌', systemContent.message);
          setAgentStatus(null);
          break;
      }
    }
  }, []);

  const handleConnect = useCallback(() => {
    console.log('[KitchenChat] WebSocket connected');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('[KitchenChat] WebSocket disconnected');
  }, []);

  // WebSocket connection
  const { isConnected, error, sendMessage } = useWebSocket({
    sessionId,
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
  });

  // Handle sending messages
  const handleSendMessage = useCallback(
    (content: string) => {
      // Add user message optimistically
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send via WebSocket
      sendMessage(content);
    },
    [sendMessage]
  );

  return (
    <div className="flex h-screen w-full">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-accent/20">
          <h1 className="text-2xl font-bold text-text">
            {recipeName || sessionName}
          </h1>
          <div className="flex items-center gap-4 mt-2">
            <p className="text-sm text-text/70">
              {messages.length} message{messages.length !== 1 ? 's' : ''}
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
                {error
                  ? 'Error'
                  : isConnected
                    ? 'Connected'
                    : 'Connecting...'}
              </span>
            </div>
          </div>
          {error && (
            <p className="text-xs text-red-500 mt-1">Connection error: {error}</p>
          )}
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <Chat
            messages={messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            agentStatus={agentStatus}
          />
        </div>
      </div>

      {/* Sidebar with ingredients and timers */}
      <div className="w-80 border-l border-accent/20 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Ingredient List */}
          {ingredients.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-text mb-3">Ingredients</h2>
              <IngredientList ingredients={ingredients} />
            </div>
          )}

          {/* Timer List */}
          {timers.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-text mb-3">Timers</h2>
              <TimerList timers={timers} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
