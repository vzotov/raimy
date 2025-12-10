import { useEffect, useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '@/hooks/useChatMessages';
import ChatMessage from './ChatMessage';

export interface ChatMessagesProps {
  messages: ChatMessageType[];
  agentStatus?: string | null;
}

/**
 * Stateless component for displaying a scrollable list of chat messages.
 * Auto-scrolls to bottom when new messages arrive.
 */
export default function ChatMessages({
  messages,
  agentStatus,
}: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or agent status changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center flex-1">
          <p className="text-text/50 text-sm">
            Start a conversation about meal planning...
          </p>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
              timestamp={message.timestamp}
            />
          ))}
          {agentStatus && (
            <div className="flex items-end gap-2 py-2 px-4 mb-2">
              <div className="flex items-center gap-1">
                <div
                  className="w-1 h-1 bg-text/40 rounded-full animate-bounce"
                  style={{ animationDelay: '0ms' }}
                />
                <div
                  className="w-1 h-1 bg-text/40 rounded-full animate-bounce"
                  style={{ animationDelay: '150ms' }}
                />
                <div
                  className="w-1 h-1 bg-text/40 rounded-full animate-bounce"
                  style={{ animationDelay: '300ms' }}
                />
              </div>
              <span className="text-sm text-text/60">{agentStatus}</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
}
