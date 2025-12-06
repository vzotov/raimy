import type { ChatAction, ChatState } from './chatTypes';

/**
 * Base reducer for chat state management.
 * Handles message addition/updates, agent status, and session name.
 */
export function chatReducer(state: ChatState, action: ChatAction): ChatState {
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

    case 'SET_AGENT_STATUS':
      return { ...state, agentStatus: action.payload };

    case 'RESET_AGENT_STATUS':
      return { ...state, agentStatus: null };

    case 'SET_SESSION_NAME':
      return { ...state, sessionName: action.payload };

    default:
      return state;
  }
}
