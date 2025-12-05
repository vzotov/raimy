import { useCallback } from 'react';
import { useChatState } from '@/hooks/useChatState';
import { useMealPlannerRecipe } from '@/hooks/useMealPlannerRecipe';
import type { ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import type { RecipeContent } from '@/types/chat-message-types';
import type { SessionMessage } from '@/types/meal-planner-session';

interface UseMealPlannerStateParams {
	sessionId: string;
	initialMessages?: SessionMessage[];
	initialRecipe?: RecipeContent;
}

/**
 * Meal planner-specific state hook that extends base chat functionality.
 * Adds: recipe state
 * Handles: recipe_update messages + all base messages
 */
export function useMealPlannerState({
	sessionId,
	initialMessages = [],
	initialRecipe,
}: UseMealPlannerStateParams) {
	// Get base chat functionality
	const {
		state: chatState,
		handleMessage: handleChatMessage,
		addMessage: addChatMessage,
	} = useChatState({
		sessionId,
		sessionType: 'meal-planner',
		initialMessages,
	});

	// Get recipe-specific functionality
	const { recipe, applyRecipeUpdate, clearRecipe } =
		useMealPlannerRecipe(initialRecipe);

	/**
	 * Handle meal planner-specific messages first, then delegate to chat handler
	 */
	const handleMessage = useCallback(
		(wsMessage: WebSocketMessage) => {
			console.log('[MealPlannerState] Received:', wsMessage);

			// Handle agent messages
			if (wsMessage.type === 'agent_message' && wsMessage.content) {
				const content = wsMessage.content;

				// Handle meal planner-specific message types
				switch (content.type) {
					case 'recipe_update':
						// Don't add to messages, just update recipe state
            applyRecipeUpdate(content);
						return; // Handled, don't delegate

					case 'session_name':
						// Initialize recipe with name if needed, then delegate to base
						if (content.name) {
							applyRecipeUpdate({
								type: 'recipe_update',
								action: 'set_metadata',
								name: content.name,
							});
						}
						// Fall through to delegate - base handler will update sessionName
						break;

					// Let base handle: text, ingredients, recipe messages
					default:
            // Delegate to base chat handler
            handleChatMessage(wsMessage);
						break;
				}
			} else {
        // Delegate to base chat handler
        handleChatMessage(wsMessage);
      }
		},
		[handleChatMessage, applyRecipeUpdate],
	);

	const addMessage = useCallback(
		(content: string) => {
			addChatMessage(content);
		},
		[addChatMessage],
	);

	return {
		state: {
			...chatState,
			recipe,
		},
		handleMessage,
		addMessage,
		applyRecipeUpdate,
		clearRecipe,
	};
}
