import classNames from 'classnames';
import type { MessageContent } from '@/types/chat-message-types';
import MessageRenderer from './message-types/MessageRenderer';

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string | MessageContent;
  timestamp?: Date;
}

/**
 * Stateless component for displaying a single chat message bubble.
 * Renders different styles for user vs assistant messages.
 * Supports both simple text and structured message types.
 */
export default function ChatMessage({
  role,
  content,
  timestamp,
}: ChatMessageProps) {
  const isUser = role === 'user';

  // Convert string content to MessageContent for backward compatibility
  const messageContent: MessageContent =
    typeof content === 'string' ? { type: 'text', content } : content;

  return (
    <div
      className={classNames('flex w-full mb-4', {
        'justify-end': isUser,
        'justify-start': !isUser,
      })}
    >
      <div
        className={classNames('max-w-[80%] rounded-2xl px-4 py-3', {
          'bg-primary text-white': isUser,
          'bg-surface text-text': !isUser,
        })}
      >
        <MessageRenderer content={messageContent} isUser={isUser} />
        {timestamp && (
          <p
            className={classNames('text-xs mt-2', {
              'text-white/70': isUser,
              'text-text/50': !isUser,
            })}
          >
            {timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
      </div>
    </div>
  );
}
