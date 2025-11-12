import { MessageContent } from '@/types/chat-message-types';
import IngredientList from './IngredientList';

export interface MessageRendererProps {
  content: MessageContent;
  isUser?: boolean;
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
export default function MessageRenderer({ content, isUser = false }: MessageRendererProps) {
  switch (content.type) {
    case 'text':
      return (
        <p className="text-sm sm:text-base whitespace-pre-wrap break-words">
          {content.content}
        </p>
      );

    case 'ingredients':
      return (
        <IngredientList
          title={content.title}
          items={content.items}
          isUser={isUser}
        />
      );

    default:
      // TypeScript exhaustiveness check - if we miss a case, this will error
      console.error('Unknown message content type:', content);
      return (
        <p className="text-sm text-red-500">
          Unknown message type
        </p>
      );
  }
}
