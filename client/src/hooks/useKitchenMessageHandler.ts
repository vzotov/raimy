import { useCallback, useReducer } from 'react';
import type { Ingredient } from '@/components/shared/IngredientList';
import type { ChatMessage } from '@/hooks/useChatMessages';
import type { ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import {
  handleIngredientsMessage,
  handleRecipeMessage,
  handleRecipeNameMessage,
  handleSystemMessage,
  handleTextMessage,
  handleTimerMessage,
  type KitchenMessageAction,
  type KitchenMessageState,
} from '@/lib/messageHandlers';
import type { SystemContent } from '@/types/chat-message-types';
import type { SessionMessage } from '@/types/meal-planner-session';

function kitchenMessageReducer(
  state: KitchenMessageState,
  action: KitchenMessageAction,
): KitchenMessageState {
  switch (action.type) {
    case 'ADD_OR_UPDATE_MESSAGE': {
      const existingIndex = state.messages.findIndex(
        (m) => m.id === action.payload.id,
      );

      if (existingIndex >= 0) {
        // Update existing message (streaming)
        const updated = [...state.messages];
        updated[existingIndex] = {
          ...updated[existingIndex],
          content: action.payload.content,
        };
        return {
          ...state,
          messages: updated,
          agentStatus: null, // Clear agent status on message
        };
      }

      // Add new message
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            id: action.payload.id,
            role: action.payload.role,
            content: action.payload.content,
            timestamp: new Date(),
          },
        ],
        agentStatus: null, // Clear agent status on message
      };
    }

    case 'SET_INGREDIENTS':
      return { ...state, ingredients: action.payload };

    case 'UPDATE_INGREDIENTS': {
      // Payload contains partial updates, merge with existing
      const updatedIngredients = state.ingredients.map((ing) => {
        const update = action.payload.find((u) => u.name === ing.name);
        return update ? { ...ing, ...update } : ing;
      });
      return { ...state, ingredients: updatedIngredients };
    }

    case 'ADD_TIMER':
      return { ...state, timers: [...state.timers, action.payload] };

    case 'SET_RECIPE_NAME':
      return { ...state, recipeName: action.payload };

    case 'SET_AGENT_STATUS':
      return { ...state, agentStatus: action.payload };

    case 'RESET_AGENT_STATUS':
      return { ...state, agentStatus: null };

    default:
      return state;
  }
}

interface UseKitchenMessageHandlerParams {
  sessionId: string;
  initialMessages?: SessionMessage[];
  initialIngredients?: Ingredient[];
}

export function useKitchenMessageHandler({
  sessionId,
  initialMessages = [],
  initialIngredients = [],
}: UseKitchenMessageHandlerParams) {
  // Convert initial messages to ChatMessage format
  const convertedMessages: ChatMessage[] = initialMessages.map(
    (msg, index) => ({
      id: `msg-${index}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp: new Date(msg.timestamp),
    }),
  );

  const [state, dispatch] = useReducer(kitchenMessageReducer, {
    messages: convertedMessages,
    ingredients: initialIngredients,
    timers: [],
    recipeName: '',
    agentStatus: null,
  });

  const handleMessage = useCallback(
    (wsMessage: WebSocketMessage) => {
      console.log('[KitchenChat] Received:', wsMessage);

      // Handle agent messages - route by content type
      if (wsMessage.type === 'agent_message' && wsMessage.content) {
        const content = wsMessage.content;
        const messageId = wsMessage.message_id || `agent-${Date.now()}`;

        // Route based on content type (application layer)
        switch (content.type) {
          case 'text':
            handleTextMessage(content, messageId, dispatch);
            break;

          case 'recipe':
            handleRecipeMessage(content, messageId, dispatch);
            break;

          case 'recipe_name':
            handleRecipeNameMessage(content, dispatch, sessionId);
            break;

          case 'ingredients':
            handleIngredientsMessage(content, dispatch);
            break;

          case 'timer':
            handleTimerMessage(content, dispatch);
            break;
        }
      }

      // Handle system messages
      if (wsMessage.type === 'system' && wsMessage.content) {
        // Type assertion needed because WebSocket types content as MessageContent
        // but for system messages it's actually SystemContent
        const systemContent = wsMessage.content as SystemContent;
        handleSystemMessage(systemContent, dispatch);
      }
    },
    [sessionId],
  );

  const addMessage = useCallback((message: ChatMessage) => {
    // Add user message optimistically
    dispatch({
      type: 'ADD_OR_UPDATE_MESSAGE',
      payload: message,
    });
  }, []);

  return {
    state,
    handleMessage,
    addMessage,
  };
}
