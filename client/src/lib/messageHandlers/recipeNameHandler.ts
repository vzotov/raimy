import type { Dispatch } from 'react';
import { updateSessionNameInCache } from '@/hooks/useSessions';
import type { RecipeNameContent } from '@/types/chat-message-types';
import type { KitchenMessageAction } from './types';

export function handleRecipeNameMessage(
  content: RecipeNameContent,
  dispatch: Dispatch<KitchenMessageAction>,
  sessionId: string,
): void {
  if (content.name) {
    // Update recipe name state
    dispatch({ type: 'SET_RECIPE_NAME', payload: content.name });

    // Update sessions list cache so the sidebar shows updated name
    updateSessionNameInCache(sessionId, content.name, 'kitchen');
  }
}
