'use client';

import { useCallback, useRef, useState } from 'react';
import type { ChatMessage } from '@/hooks/useChatMessages';
import ChatInput, { type ChatInputHandle } from './ChatInput';
import ChatMessages from './ChatMessages';

export interface ChatProps {
  sessionId?: string;
  messages?: ChatMessage[];
  onSendMessage?: (message: string) => void;
  isConnected?: boolean;
  agentStatus?: string | null;
  onFocusInput?: () => void;
  onMessageAction?: (action: string) => void;
  placeholder?: string;
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
  onFocusInput,
  onMessageAction,
  placeholder = 'Type a message...',
}: ChatProps) {
  const [isSending, setIsSending] = useState(false);
  const inputRef = useRef<ChatInputHandle>(null);

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

  // Default implementations for callbacks
  const defaultFocusInput = useCallback(() => {
    inputRef.current?.focus();
  }, []);

  const defaultMessageAction = useCallback(
    (action: string) => {
      handleSend(action);
    },
    [handleSend],
  );

  const isDisabled = !isConnected || isSending;

  return (
    <div className="flex flex-col h-full">
      <ChatMessages
        messages={messages}
        agentStatus={agentStatus}
        onFocusInput={onFocusInput || defaultFocusInput}
        onMessageAction={onMessageAction || defaultMessageAction}
      />
      <ChatInput
        ref={inputRef}
        onSend={handleSend}
        disabled={isDisabled}
        placeholder={isConnected ? placeholder : 'Connecting...'}
      />
    </div>
  );
}
