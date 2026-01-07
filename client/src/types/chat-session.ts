import type {
  ChatIngredient,
  MessageContent,
  RecipeContent,
} from './chat-message-types';

export interface ChatSession {
  id: string;
  user_id: string;
  session_name: string;
  session_type: 'recipe-creator' | 'kitchen';
  room_name?: string; // Optional - LiveKit remnant
  ingredients?: ChatIngredient[];
  recipe?: RecipeContent | null; // Work-in-progress recipe data
  recipe_id?: string | null; // Saved recipe reference
  created_at: string;
  updated_at: string;
}

export interface ChatSessionWithMessages extends ChatSession {
  messages: SessionMessage[];
}

export interface SessionMessage {
  role: 'user' | 'assistant';
  content: MessageContent; // Always structured content
  timestamp: string;
}

export interface CreateSessionResponse {
  message: string;
  session: ChatSession;
}

export interface ListSessionsResponse {
  sessions: ChatSession[];
  count: number;
}

export interface GetSessionResponse {
  session: ChatSessionWithMessages;
}

export interface UpdateSessionNameRequest {
  session_name: string;
}

export interface UpdateSessionNameResponse {
  message: string;
  session_id: string;
  session_name: string;
}

export interface DeleteSessionResponse {
  message: string;
  session_id: string;
}
