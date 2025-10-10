'use client';

import { useConnectionState, useChat } from '@livekit/components-react';
import { useChatMessages } from '@/hooks/useChatMessages';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import { useEffect } from 'react';
import { ChatMessage } from '@/hooks/useChatMessages';

export interface ChatProps {
  showDebugPanel?: boolean;
  debugMessages?: ChatMessage[];
  onDebugMessagesChange?: (messages: ChatMessage[]) => void;
}

/**
 * Stateful chat container component.
 * Manages chat state using LiveKit hooks and renders chat UI.
 * Supports debug mode for testing message types without LLM.
 */
export default function Chat({ showDebugPanel = false, debugMessages = [], onDebugMessagesChange }: ChatProps) {
  const liveMessages = useChatMessages();
  const connectionState = useConnectionState();
  const { send, isSending, chatMessages } = useChat();

  // Use debug messages when in debug mode, otherwise use live messages
  const messages = showDebugPanel ? debugMessages : liveMessages;

  // Debug logging
  useEffect(() => {
    console.log('[Chat] Connection state:', connectionState);
  }, [connectionState]);

  useEffect(() => {
    console.log('[Chat] Raw chatMessages from useChat:', chatMessages);
    console.log('[Chat] Processed messages from useChatMessages:', liveMessages);
  }, [chatMessages, liveMessages]);

  const handleSend = async (message: string) => {
    try {
      // Send via LiveKit chat (handles encoding automatically)
      await send(message);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const isConnected = connectionState === 'connected';

  return (
    <div className="flex flex-col h-full">
      <ChatMessages messages={messages} />
      <ChatInput
        onSend={handleSend}
        disabled={!isConnected || isSending}
        placeholder={
          isConnected
            ? 'Ask about meal ideas, recipes, or ingredients...'
            : 'Connecting to chat...'
        }
      />
    </div>
  );
}
