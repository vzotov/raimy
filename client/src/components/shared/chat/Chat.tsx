'use client';

import { useCallback, useState } from 'react';
import type { ChatMessage } from '@/hooks/useChatMessages';
import ChatInput from './ChatInput';
import ChatMessages from './ChatMessages';

export interface ChatProps {
  sessionId?: string;
  messages?: ChatMessage[];
  onSendMessage?: (message: string) => void;
  isConnected?: boolean;
  agentStatus?: string | null;
}

/**
 * Stateful chat container component.
 * Manages chat state and renders chat UI via WebSocket.
 * Supports debug mode for testing message types without LLM.
 */
export default function Chat({
  messages = [],
  onSendMessage,
  isConnected = false,
  agentStatus = null,
}: ChatProps) {
  const [isSending, setIsSending] = useState(false);

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
    [onSendMessage],
  );

  const isDisabled = !isConnected || isSending;

  return (
    <div className="flex flex-col h-full">
      <ChatMessages messages={messages} agentStatus={agentStatus} />
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
