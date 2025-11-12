'use client';

import { useConnectionState, useChat } from '@livekit/components-react';
import { useChatMessages } from '@/hooks/useChatMessages';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import { useCallback, useMemo } from 'react';
import { ChatMessage } from '@/hooks/useChatMessages';
import { SessionMessage } from '@/types/meal-planner-session';

export interface ChatProps {
  showDebugPanel?: boolean;
  debugMessages?: ChatMessage[];
  sessionId?: string;
  initialMessages?: SessionMessage[];
}

/**
 * Stateful chat container component.
 * Manages chat state using LiveKit hooks and renders chat UI.
 * Supports debug mode for testing message types without LLM.
 */
export default function Chat({
  showDebugPanel = false,
  debugMessages = [],
  initialMessages = [],
}: ChatProps) {
  const liveMessages = useChatMessages();
  const connectionState = useConnectionState();
  const { send, isSending } = useChat();

  // Merge initial messages from database with live messages from LiveKit
  // This ensures persisted messages appear in the UI
  const messages = useMemo(() => {
    if (showDebugPanel) return debugMessages;

    // Convert initial messages to ChatMessage format
    const dbMessages: ChatMessage[] = initialMessages.map((msg, idx) => ({
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.timestamp),
      id: `db-${idx}-${msg.timestamp}`,
    }));

    // Combine with live messages, removing duplicates by content
    const combined = [...dbMessages];
    const existingContents = new Set(dbMessages.map(m =>
      typeof m.content === 'string' ? m.content : JSON.stringify(m.content)
    ));

    liveMessages.forEach(msg => {
      const msgContent = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
      if (!existingContents.has(msgContent)) {
        combined.push(msg);
        existingContents.add(msgContent);
      }
    });

    // Sort by timestamp
    combined.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    return combined;
  }, [showDebugPanel, debugMessages, initialMessages, liveMessages]);

  const handleSend = useCallback(async (message: string) => {
    try {
      await send(message);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [send]);

  const isConnected = connectionState === 'connected';
  const isDisabled = !isConnected || isSending;

  return (
    <div className="flex flex-col h-full">
      <ChatMessages messages={messages} />
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
