import { useCallback, useReducer, useState } from 'react';
import type { ChatMessage } from '@/hooks/useChatMessages';
import type { ChatMessage as WebSocketMessage } from '@/hooks/useWebSocket';
import { chatReducer } from '@/lib/messageHandlers/chatReducer';
import { useMealPlannerRecipe } from '@/hooks/useMealPlannerRecipe';
import { updateSessionNameInCache } from '@/hooks/useSessions';
import type { SessionMessage } from '@/types/chat-session';
import type { Recipe } from '@/types/recipe';

interface Params {
  sessionId: string;
  initialMessages?: SessionMessage[];
  initialFinished?: boolean;
  initialRecipe?: Recipe | null;
  initialIsChanged?: boolean;
}

function convertInitialMessages(messages: SessionMessage[]): ChatMessage[] {
  return messages.map((msg, index) => {
    const timestamp = new Date(msg.timestamp);
    return {
      id: `msg-${index}-${timestamp.getTime()}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp,
    };
  });
}

function buildMessage(content: WebSocketMessage['content'], messageId: string, role: 'user' | 'assistant'): ChatMessage {
  return {
    id: messageId,
    role,
    content: content!,
    timestamp: new Date(),
  };
}

export function useUnifiedChatState({
  sessionId,
  initialMessages = [],
  initialFinished = false,
  initialRecipe = null,
  initialIsChanged = false,
}: Params) {
  const [messages, dispatch] = useReducer(chatReducer, {
    messages: convertInitialMessages(initialMessages),
    agentStatus: null,
    sessionName: '',
  });

  const [agentStatus, setAgentStatus] = useState<string | null>(null);
  const [sessionName, setSessionName] = useState('');
  const [cookingComplete, setCookingComplete] = useState(initialFinished);
  const [cookingStarted, setCookingStarted] = useState(false);

  const { recipe, isRecipeChanged, applyRecipeUpdate, setRecipe, resetChangedFlag } =
    useMealPlannerRecipe(initialRecipe, initialIsChanged);

  const handleMessage = useCallback(
    (wsMessage: WebSocketMessage) => {
      if (wsMessage.type === 'agent_message' && wsMessage.content) {
        const content = wsMessage.content;
        const messageId = wsMessage.message_id || `agent-${Date.now()}`;

        switch (content.type) {
          case 'recipe_update':
            applyRecipeUpdate(content);
            return;

          case 'cooking_complete':
            setCookingComplete(true);
            return;

          case 'kitchen-step':
            setCookingStarted(true);
            dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: buildMessage(content, messageId, 'assistant') });
            setAgentStatus(null);
            return;

          case 'recipe_saved':
            if (recipe && content.recipe_id) {
              setRecipe({ ...recipe, id: content.recipe_id });
            }
            return;

          case 'session_name':
            setSessionName(content.name);
            updateSessionNameInCache(sessionId, content.name, 'chat');
            return;

          case 'text':
          case 'selector':
            dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: buildMessage(content, messageId, 'assistant') });
            setAgentStatus(null);
            return;

          default:
            // ingredients, timer, etc. — add to messages if unknown
            dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: buildMessage(content, messageId, 'assistant') });
            setAgentStatus(null);
        }
      }

      if (wsMessage.type === 'system' && wsMessage.content) {
        const sys = wsMessage.content;
        if (sys.type === 'thinking') setAgentStatus(sys.message ?? null);
        else if (sys.type === 'connected' || sys.type === 'error') setAgentStatus(null);
      }
    },
    [sessionId, applyRecipeUpdate, recipe, setRecipe],
  );

  const addMessage = useCallback((content: string) => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: { type: 'text', content },
      timestamp: new Date(),
    };
    dispatch({ type: 'ADD_OR_UPDATE_MESSAGE', payload: userMessage });
    setAgentStatus('thinking');
  }, []);

  return {
    messages: messages.messages,
    agentStatus,
    sessionName,
    cookingComplete,
    cookingStarted,
    recipe,
    isRecipeChanged,
    handleMessage,
    addMessage,
    setRecipe,
    resetChangedFlag,
    applyRecipeUpdate,
  };
}
