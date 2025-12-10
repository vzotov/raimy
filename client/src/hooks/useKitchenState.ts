import { useCallback, useReducer } from 'react';
import type { Ingredient } from '@/components/shared/IngredientList';
import { useChatState } from '@/hooks/useChatState';
import type { ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import {
  handleIngredientsMessage,
  handleTimerMessage,
} from '@/lib/messageHandlers';
import type {
  KitchenMessageAction,
  KitchenMessageState,
} from '@/lib/messageHandlers/types';
import type { SessionMessage } from '@/types/meal-planner-session';

interface UseKitchenStateParams {
  sessionId: string;
  initialMessages?: SessionMessage[];
  initialIngredients?: Ingredient[];
}

/**
 * Kitchen-specific state hook that extends base chat functionality.
 * Adds: ingredients, timers
 * Handles: ingredients, timer messages + all base messages
 */
export function useKitchenState({
  sessionId,
  initialMessages = [],
  initialIngredients = [],
}: UseKitchenStateParams) {
  // Get base chat functionality
  const {
    state: chatState,
    handleMessage: handleChatMessage,
    addMessage: addChatMessage,
  } = useChatState({
    sessionId,
    sessionType: 'kitchen',
    initialMessages,
  });

  // Extend with kitchen-specific state
  const [kitchenSpecificState, kitchenDispatch] = useReducer(
    (
      state: Pick<KitchenMessageState, 'ingredients' | 'timers'>,
      action: KitchenMessageAction,
    ) => {
      switch (action.type) {
        case 'SET_INGREDIENTS':
          return { ...state, ingredients: action.payload };

        case 'UPDATE_INGREDIENTS': {
          const updatedIngredients = state.ingredients.map((ing) => {
            const update = action.payload.find((u) => u.name === ing.name);
            return update ? { ...ing, ...update } : ing;
          });
          return { ...state, ingredients: updatedIngredients };
        }

        case 'ADD_TIMER':
          return { ...state, timers: [...state.timers, action.payload] };

        default:
          return state;
      }
    },
    {
      ingredients: initialIngredients,
      timers: [],
    },
  );

  // Combine chat state with kitchen-specific state
  const state: KitchenMessageState = {
    ...chatState,
    ...kitchenSpecificState,
  };

  /**
   * Handle kitchen-specific messages first, then delegate to chat handler
   */
  const handleMessage = useCallback(
    (wsMessage: WebSocketMessage) => {
      console.log('[KitchenState] Received:', wsMessage);

      // Handle agent messages
      if (wsMessage.type === 'agent_message' && wsMessage.content) {
        const content = wsMessage.content;

        // Handle kitchen-specific message types
        switch (content.type) {
          case 'ingredients':
            handleIngredientsMessage(content, kitchenDispatch);
            return; // Handled, don't delegate

          case 'timer':
            handleTimerMessage(content, kitchenDispatch);
            return; // Handled, don't delegate

          default:
            // Delegate to base chat handler for text, session_name, etc.
            handleChatMessage(wsMessage);
        }
      } else {
        // System messages and others - delegate to base
        handleChatMessage(wsMessage);
      }
    },
    [handleChatMessage, kitchenDispatch],
  );

  const addMessage = useCallback(
    (content: string) => {
      addChatMessage(content);
    },
    [addChatMessage],
  );

  return {
    state,
    handleMessage,
    addMessage,
  };
}
