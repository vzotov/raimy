import { useCallback, useReducer } from 'react';
import type { ChatMessage } from '@/hooks/useChatMessages';
import type { ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import {
  chatReducer,
  handleSessionNameMessage,
  handleSystemMessage,
  handleTextMessage,
} from '@/lib/messageHandlers';
import type { ChatAction, ChatState } from '@/lib/messageHandlers/chatTypes';
import type { SystemContent } from '@/types/chat-message-types';
import type { SessionMessage } from '@/types/meal-planner-session';

interface UseChatStateParams {
  sessionId: string;
  sessionType: 'meal-planner' | 'kitchen';
  initialMessages?: SessionMessage[];
  initialSessionName?: string;
}

interface UseChatStateReturn {
  state: ChatState;
  dispatch: React.Dispatch<ChatAction>;
  handleMessage: (wsMessage: WebSocketMessage) => void;
  addMessage: (content: string) => void;
}

/**
 * Base chat state hook that manages common chat functionality.
 * Handles: messages, agentStatus, sessionName
 * Message types: text, session_name, system
 */
export function useChatState({
  sessionId,
  sessionType,
  initialMessages = [],
  initialSessionName = '',
}: UseChatStateParams): UseChatStateReturn {
  // Convert initial messages to ChatMessage format
  const convertedMessages: ChatMessage[] = initialMessages.map((msg, index) => {
    const timestamp = new Date(msg.timestamp);
    return {
      id: `msg-${index}-${timestamp.getTime()}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp,
    };
  });

  const [state, dispatch] = useReducer(chatReducer, {
    messages: convertedMessages,
    agentStatus: null,
    sessionName: initialSessionName,
  });

  /**
   * Handle common message types: text, session_name, system
   * This is meant to be used as a fallback by specialized hooks
   */
  const handleMessage = useCallback(
    (wsMessage: WebSocketMessage) => {
      console.log('[ChatState] Handling message:', wsMessage);

      // Handle agent messages - route by content type
      if (wsMessage.type === 'agent_message' && wsMessage.content) {
        const content = wsMessage.content;
        const messageId = wsMessage.message_id || `agent-${Date.now()}`;

        switch (content.type) {
          case 'text':
            handleTextMessage(content, messageId, dispatch);
            break;

          case 'session_name':
            handleSessionNameMessage(content, dispatch, sessionId, sessionType);
            break;

          // Other message types should be handled by specialized hooks
          default:
            console.warn('[ChatState] Unhandled message type:', content.type);
        }
      }

      // Handle system messages
      if (wsMessage.type === 'system' && wsMessage.content) {
        const systemContent = wsMessage.content as SystemContent;
        handleSystemMessage(systemContent, dispatch);
      }
    },
    [sessionId, sessionType],
  );

  const addMessage = useCallback((content: string) => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    dispatch({
      type: 'ADD_OR_UPDATE_MESSAGE',
      payload: userMessage,
    });
  }, []);

  return {
    state,
    dispatch,
    handleMessage,
    addMessage,
  };
}
