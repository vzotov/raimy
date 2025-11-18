'use client';

import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import { useCallback, useState } from 'react';
import { ChatMessage } from '@/hooks/useChatMessages';

export interface ChatProps {
  showDebugPanel?: boolean;
  debugMessages?: ChatMessage[];
  sessionId?: string;
  messages?: ChatMessage[];
  onSendMessage?: (message: string) => void;
  isConnected?: boolean;
}

/**
 * Stateful chat container component.
 * Manages chat state and renders chat UI via WebSocket.
 * Supports debug mode for testing message types without LLM.
 */
export default function Chat({
  showDebugPanel = false,
  debugMessages = [],
  messages = [],
  onSendMessage,
  isConnected = false,
}: ChatProps) {
  const [isSending, setIsSending] = useState(false);

  // Use debug messages if debug panel is shown, otherwise use regular messages
  const displayMessages = showDebugPanel ? debugMessages : messages;

  const handleSend = useCallback(
    async (message: string) => {
      if (!onSendMessage) return;

      try {
        setIsSending(true);
        onSendMessage(message);
      } catch (error) {
        console.error('Failed to send message:', error);
      } finally {
        // Reset sending state after a short delay
        setTimeout(() => setIsSending(false), 500);
      }
    },
    [onSendMessage]
  );

  const isDisabled = !isConnected || isSending;

  return (
    <div className="flex flex-col h-full">
      <ChatMessages messages={displayMessages} />
      <ChatInput
        onSend={handleSend}
        disabled={isDisabled}
        placeholder={
          isConnected
            ? 'Ask about meal ideas, recipes, or ingredients...'
            : 'Connecting to chat...'
        }
      />
    </div>
  );
}
