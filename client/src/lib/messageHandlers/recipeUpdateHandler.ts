import type { RecipeUpdateContent } from '@/types/chat-message-types';

/**
 * Handle recipe update messages by forwarding them to the recipe hook
 */
export function handleRecipeUpdateMessage(
  content: RecipeUpdateContent,
  applyUpdate: (update: RecipeUpdateContent) => void,
): void {
  applyUpdate(content);
}
