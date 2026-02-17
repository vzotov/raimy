import type { MessageContent } from '@/types/chat-message-types';
import MessageConfirmationButtons from './MessageConfirmationButtons';
import MessageSelectorButtons from './MessageSelectorButtons';

export interface MessageRendererProps {
  content: MessageContent;
  isUser?: boolean;
  isLastMessage?: boolean;
  onFocusInput?: () => void;
  onMessageAction?: (action: string) => void;
}

/**
 * Central message renderer that uses a switch statement to render different message types.
 * This is the main extension point for adding new message types.
 *
 * To add a new message type:
 * 1. Define the type in chat-message-types.ts
 * 2. Create a component for the type
 * 3. Add a case to the switch statement below
 */
export default function MessageRenderer({
  content,
  isUser = false,
  isLastMessage,
  onFocusInput,
  onMessageAction,
}: MessageRendererProps) {
  switch (content.type) {
    case 'text':
      return (
        <p className="text-sm sm:text-base whitespace-pre-wrap break-words">
          {content.content}
        </p>
      );

    case 'kitchen-step':
      return (
        <div>
          {content.image_url && (
            <div className="mb-3 rounded-xl overflow-hidden">
              <img src={content.image_url} alt="" className="w-full h-auto object-cover" loading="lazy" />
            </div>
          )}
          <p className="text-sm sm:text-base whitespace-pre-wrap break-words">
            {content.message}
          </p>
          {isLastMessage && onFocusInput && onMessageAction && (
            <MessageConfirmationButtons
              onAskQuestion={onFocusInput}
              onSendDone={() => onMessageAction(content.next_step_prompt)}
              doneLabel={content.next_step_prompt}
            />
          )}
        </div>
      );

    case 'selector':
      return (
        <div>
          <p className="text-sm sm:text-base whitespace-pre-wrap break-words">
            {content.message}
          </p>
          {isLastMessage && onMessageAction && (
            <MessageSelectorButtons
              options={content.options}
              onSelect={onMessageAction}
            />
          )}
        </div>
      );

    default:
      // TypeScript exhaustiveness check - if we miss a case, this will error
      console.error('Unknown message content type:', content);
      return <p className="text-sm text-red-500">Unknown message type</p>;
  }
}
