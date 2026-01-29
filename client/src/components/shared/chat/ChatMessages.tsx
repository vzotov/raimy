import { useEffect, useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '@/hooks/useChatMessages';
import ChatMessage from './ChatMessage';
import ThinkingIndicator from './ThinkingIndicator';

export interface ChatMessagesProps {
  messages: ChatMessageType[];
  agentStatus?: string | null;
  onFocusInput?: () => void;
  onMessageAction?: (action: string) => void;
}

/**
 * Stateless component for displaying a scrollable list of chat messages.
 * Auto-scrolls to bottom when new messages arrive.
 */
export default function ChatMessages({
  messages,
  agentStatus,
  onFocusInput,
  onMessageAction,
}: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or agent status changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  const lastMessageIndex = messages.length - 1;

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center flex-1"></div>
      ) : (
        <>
          {messages.map((message, index) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
              timestamp={message.timestamp}
              isLastMessage={index === lastMessageIndex}
              onFocusInput={onFocusInput}
              onMessageAction={onMessageAction}
            />
          ))}
          {agentStatus && <ThinkingIndicator message={agentStatus} />}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
}
