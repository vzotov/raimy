import type { ChatMessage } from '@/hooks/useChatMessages';

/**
 * Base chat state shared across all chat types
 */
export interface ChatState {
  messages: ChatMessage[];
  agentStatus: string | null;
  sessionName: string;
}

/**
 * Base chat actions for common message handling
 */
export type ChatAction =
  | {
      type: 'ADD_OR_UPDATE_MESSAGE';
      payload: Omit<ChatMessage, 'timestamp'>;
    }
  | { type: 'SET_AGENT_STATUS'; payload: string | null }
  | { type: 'RESET_AGENT_STATUS' }
  | { type: 'SET_SESSION_NAME'; payload: string };
