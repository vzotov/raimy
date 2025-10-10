import classNames from 'classnames';

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

/**
 * Stateless component for displaying a single chat message bubble.
 * Renders different styles for user vs assistant messages.
 */
export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={classNames('flex w-full mb-4', {
      'justify-end': isUser,
      'justify-start': !isUser,
    })}>
      <div className={classNames('max-w-[80%] rounded-2xl px-4 py-3', {
        'bg-primary text-white': isUser,
        'bg-surface text-text': !isUser,
      })}>
        <p className="text-sm sm:text-base whitespace-pre-wrap break-words">
          {content}
        </p>
        {timestamp && (
          <p className={classNames('text-xs mt-1', {
            'text-white/70': isUser,
            'text-text/50': !isUser,
          })}>
            {/* TODO: Fix invalid date display for agent messages */}
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  );
}
