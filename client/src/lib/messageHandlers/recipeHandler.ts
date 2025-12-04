import type { Dispatch } from 'react';
import type { MessageContent } from '@/types/chat-message-types';
import type { KitchenMessageAction } from './types';

export function handleRecipeMessage(
  content: MessageContent,
  messageId: string,
  dispatch: Dispatch<KitchenMessageAction>,
): void {
  // Add recipe message to chat history
  dispatch({
    type: 'ADD_OR_UPDATE_MESSAGE',
    payload: {
      id: messageId,
      role: 'assistant',
      content,
    },
  });
}
