'use client';

import { useConnectionState, useChat } from '@livekit/components-react';
import { useChatMessages } from '@/hooks/useChatMessages';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import { useEffect } from 'react';

/**
 * Stateful chat container component.
 * Manages chat state using LiveKit hooks and renders chat UI.
 */
export default function Chat() {
  const messages = useChatMessages();
  const connectionState = useConnectionState();
  const { send, isSending, chatMessages } = useChat();

  // Debug logging
  useEffect(() => {
    console.log('[Chat] Connection state:', connectionState);
  }, [connectionState]);

  useEffect(() => {
    console.log('[Chat] Raw chatMessages from useChat:', chatMessages);
    console.log('[Chat] Processed messages from useChatMessages:', messages);
  }, [chatMessages, messages]);

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
