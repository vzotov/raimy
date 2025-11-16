'use client';

import { useState } from 'react';
import Chat from '@/components/shared/chat/Chat';
import ChatDebugPanel from '@/components/debug/ChatDebugPanel';
import classNames from 'classnames';
import { ChatMessage } from '@/hooks/useChatMessages';
import { MessageContent } from '@/types/chat-message-types';
import { SessionMessage } from '@/types/meal-planner-session';
import { useWebSocket } from '@/hooks/useWebSocket';

interface MealPlannerProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
}

export default function MealPlanner({
  sessionId,
  sessionName,
  initialMessages = [],
}: MealPlannerProps) {
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  const [debugMessages, setDebugMessages] = useState<ChatMessage[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    // Convert initial messages to ChatMessage format
    return initialMessages.map((msg) => ({
      id: `initial-${msg.id}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp: new Date(msg.created_at),
    }));
  });

  // WebSocket connection
  const { isConnected, error, sendMessage } = useWebSocket({
    sessionId,
    onMessage: (wsMessage) => {
      console.log('[MealPlanner] Received WebSocket message:', wsMessage);

      if (wsMessage.type === 'agent_message' && wsMessage.content) {
        const newMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: wsMessage.content,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, newMessage]);
      }
    },
    onConnect: () => {
      console.log('[MealPlanner] WebSocket connected');
    },
    onDisconnect: () => {
      console.log('[MealPlanner] WebSocket disconnected');
    },
  });

  const handleAddDebugMessage = (role: 'user' | 'assistant', content: MessageContent) => {
    const newMessage: ChatMessage = {
      id: `debug-${Date.now()}-${Math.random()}`,
      role,
      content,
      timestamp: new Date(),
    };
    setDebugMessages((prev) => [...prev, newMessage]);
  };

  const handleClearMessages = () => {
    setDebugMessages([]);
  };

  const handleSendMessage = (content: string) => {
    // Add user message to state immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send via WebSocket
    sendMessage(content);
  };

  return (
    <div className={classNames('flex flex-1 flex-col w-full max-w-7xl mx-auto')}>
      {/* Header */}
      <div className="p-4 border-b border-accent/20 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text">{sessionName}</h1>
          <p className="text-sm text-text/70 mt-1">
            {messages.length > 0
              ? `${messages.length} message${messages.length !== 1 ? 's' : ''} in this session`
              : 'Plan your meals with AI assistance'}
          </p>
          {!isConnected && !error && (
            <p className="text-xs text-primary mt-2">Connecting to assistant...</p>
          )}
          {isConnected && (
            <p className="text-xs text-green-500 mt-2">Connected • Ready to chat</p>
          )}
          {error && (
            <p className="text-xs text-red-500 mt-2">Error: {error}</p>
          )}
        </div>

        {/* Debug toggle */}
        <button
          onClick={() => setShowDebugPanel(!showDebugPanel)}
          className={classNames(
            'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
            {
              'bg-primary text-white': showDebugPanel,
              'bg-accent/20 text-text hover:bg-accent/30': !showDebugPanel,
            }
          )}
        >
          {showDebugPanel ? '✓ Debug Mode' : 'Debug Mode'}
        </button>
      </div>

      {/* Main Chat Area with Optional Debug Panel */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          <Chat
            showDebugPanel={showDebugPanel}
            debugMessages={debugMessages}
            sessionId={sessionId}
            messages={messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
          />
        </div>

        {showDebugPanel && (
          <ChatDebugPanel
            onAddMessage={handleAddDebugMessage}
            onClear={handleClearMessages}
          />
        )}
      </div>
    </div>
  );
}
