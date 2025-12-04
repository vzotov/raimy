'use client';

import classNames from 'classnames';
import { useCallback, useState } from 'react';
import Chat from '@/components/shared/chat/Chat';
import type { ChatMessage } from '@/hooks/useChatMessages';
import {
  useWebSocket,
  type ChatMessage as WebSocketMessage,
} from '@/hooks/useWebSocket';
import type { MessageContent } from '@/types/chat-message-types';
import type { SessionMessage } from '@/types/meal-planner-session';

interface MealPlannerChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
}

export default function MealPlannerChat({
  sessionId,
  sessionName,
  initialMessages = [],
}: MealPlannerChatProps) {
  // Convert initial messages to ChatMessage format
  // Messages from DB are already structured - no parsing needed
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    initialMessages.map((msg, index) => ({
      id: `msg-${index}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content, // Already MessageContent from backend
      timestamp: new Date(msg.timestamp),
    })),
  );

  // Memoize WebSocket callbacks to prevent reconnections
  const handleMessage = useCallback((wsMessage: WebSocketMessage) => {
    console.log('[MealPlannerChat] Received:', wsMessage);

    if (wsMessage.type === 'agent_message' && wsMessage.content) {
      const content = wsMessage.content;
      // Handle MessageContent types (text, ingredients, recipe)
      // Meal planner doesn't handle tool responses like recipe_name, timer, etc.
      if (content.type === 'text') {
        // Handle text messages with streaming support
        const messageId = wsMessage.message_id || `agent-${Date.now()}`;

        setMessages((prev) => {
          const existingIndex = prev.findIndex((m) => m.id === messageId);

          if (existingIndex >= 0) {
            // Update existing message with new content
            const updated = [...prev];
            updated[existingIndex] = {
              ...updated[existingIndex],
              content: content as MessageContent,
            };
            return updated;
          } else {
            // Create new message
            return [
              ...prev,
              {
                id: messageId,
                role: 'assistant',
                content: content as MessageContent,
                timestamp: new Date(),
              },
            ];
          }
        });
      } else if (content.type === 'ingredients' || content.type === 'recipe') {
        // Add ingredients and recipe messages normally (no streaming)
        const newMessage: ChatMessage = {
          id: wsMessage.message_id || `agent-${Date.now()}`,
          role: 'assistant',
          content: content as MessageContent,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, newMessage]);
      }
    }

    // Handle system messages (log for now, could show toasts/banners)
    if (wsMessage.type === 'system' && wsMessage.content) {
      const systemContent = wsMessage.content;
      switch (systemContent.type) {
        case 'connected':
          console.log('✅', systemContent.message);
          break;
        case 'error':
          console.error('❌', systemContent.message);
          break;
      }
    }
  }, []);

  const handleConnect = useCallback(() => {
    console.log('[MealPlannerChat] WebSocket connected');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('[MealPlannerChat] WebSocket disconnected');
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
    [sendMessage],
  );

  return (
    <div className="flex flex-col h-screen max-w-7xl mx-auto">
      {/* Header */}
      <div className="p-4 border-b border-accent/20">
        <h1 className="text-2xl font-bold text-text">{sessionName}</h1>
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
              {error ? 'Error' : isConnected ? 'Connected' : 'Connecting...'}
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
        />
      </div>
    </div>
  );
}
