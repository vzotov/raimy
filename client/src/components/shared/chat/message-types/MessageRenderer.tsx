import ReactMarkdown from 'react-markdown';
import type { MessageContent, ShoppingListItem } from '@/types/chat-message-types';
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
        <div className="prose prose-sm sm:prose-base prose-neutral max-w-none break-words">
          <ReactMarkdown>{content.content}</ReactMarkdown>
        </div>
      );

    case 'kitchen-step':
      return (
        <div>
          {content.image_url && (
            <div className="mb-3 rounded-xl overflow-hidden">
              <img src={content.image_url} alt="" className="w-full h-auto object-cover" loading="lazy" />
            </div>
          )}
          <div className="prose prose-sm sm:prose-base prose-neutral max-w-none break-words">
            <ReactMarkdown>{content.message}</ReactMarkdown>
          </div>
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

    case 'shopping_list':
      return (
        <div>
          {content.recipe_name && (
            <p className="mb-2 text-sm font-medium">{content.recipe_name}</p>
          )}
          <ul className="space-y-1">
            {content.items.map((item: ShoppingListItem, i: number) => (
              <li key={i} className="text-sm">
                {[item.amount, item.unit, item.name].filter(Boolean).join(' ')}
              </li>
            ))}
          </ul>
        </div>
      );

    default:
      // TypeScript exhaustiveness check - if we miss a case, this will error
      console.error('Unknown message content type:', content);
      return <p className="text-sm text-red-500">Unknown message type</p>;
  }
}
