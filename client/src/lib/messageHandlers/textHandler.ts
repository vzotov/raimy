import type { Dispatch } from 'react';
import type { MessageContent } from '@/types/chat-message-types';
import type { KitchenMessageAction } from './types';

export function handleTextMessage(
  content: MessageContent,
  messageId: string,
  dispatch: Dispatch<KitchenMessageAction>,
): void {
  // Just dispatch - reducer handles checking if message exists and clearing agent status
  dispatch({
    type: 'ADD_OR_UPDATE_MESSAGE',
    payload: {
      id: messageId,
      role: 'assistant',
      content,
    },
  });
}
