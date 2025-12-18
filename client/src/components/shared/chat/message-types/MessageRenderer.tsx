import type { MessageContent } from '@/types/chat-message-types';
import IngredientList from './IngredientList';
import MessageConfirmationButtons from './MessageConfirmationButtons';
import RecipeMessage from './RecipeMessage';

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
          <p className="text-sm sm:text-base whitespace-pre-wrap break-words">
            {content.content}
          </p>
          {isLastMessage && onFocusInput && onMessageAction && (
            <MessageConfirmationButtons
              onAskQuestion={onFocusInput}
              onSendDone={() => onMessageAction('done!')}
            />
          )}
        </div>
      );

    case 'ingredients':
      return (
        <IngredientList
          title={content.title}
          items={content.items}
          isUser={isUser}
        />
      );

    case 'recipe':
      return <RecipeMessage recipe={content} isUser={isUser} />;

    case 'recipe_update':
      // recipe_update messages are not rendered in chat - they only update the sidebar
      // They are handled separately in MealPlannerChat
      return null;

    default:
      // TypeScript exhaustiveness check - if we miss a case, this will error
      console.error('Unknown message content type:', content);
      return <p className="text-sm text-red-500">Unknown message type</p>;
  }
}
