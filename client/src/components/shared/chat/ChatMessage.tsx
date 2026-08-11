import classNames from 'classnames';
import type { MessageContent } from '@/types/chat-message-types';
import MessageRenderer from './message-types/MessageRenderer';

export interface ChatMessageProps {
  role: 'user' | 'assistant' | 'system';
  content: MessageContent;
  timestamp?: Date;
  isLastMessage?: boolean;
  onFocusInput?: () => void;
  onMessageAction?: (action: string) => void;
}

/**
 * Stateless component for displaying a single chat message bubble.
 * Renders different styles for user, assistant, and system messages.
 * Supports both simple text and structured message types.
 */
export default function ChatMessage({
  role,
  content,
  timestamp,
  isLastMessage,
  onFocusInput,
  onMessageAction,
}: ChatMessageProps) {
  const isUser = role === 'user';
  const isSystem = role === 'system';

  return (
    <div
      className={classNames('flex w-full mb-4', {
        'justify-end': isUser,
        'justify-start': role === 'assistant',
        'justify-center': isSystem,
      })}
    >
      <div
        className={classNames('rounded-2xl px-4 py-3', {
          'max-w-[80%] bg-primary text-white': isUser,
          'max-w-[80%] bg-surface text-text': role === 'assistant',
          'max-w-[90%] bg-red-100 text-red-800 text-center': isSystem,
        })}
      >
        <MessageRenderer
          content={content}
          isUser={isUser}
          isLastMessage={isLastMessage}
          onFocusInput={onFocusInput}
          onMessageAction={onMessageAction}
        />
        {timestamp && !isSystem && (
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
