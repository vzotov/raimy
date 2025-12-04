import type { Dispatch } from 'react';
import type { IngredientsContent } from '@/types/chat-message-types';
import type { KitchenMessageAction } from './types';

export function handleIngredientsMessage(
  content: IngredientsContent,
  dispatch: Dispatch<KitchenMessageAction>,
): void {
  if (content.action === 'set' && content.items) {
    // Set ingredients list
    dispatch({ type: 'SET_INGREDIENTS', payload: content.items });
  } else if (content.action === 'update' && content.items) {
    // Dispatch partial updates - reducer will merge with existing
    dispatch({ type: 'UPDATE_INGREDIENTS', payload: content.items });
  }
}
