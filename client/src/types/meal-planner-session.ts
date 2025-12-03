import { MessageContent, ChatIngredient } from './chat-message-types';

export interface MealPlannerSession {
  id: string;
  user_id: string;
  session_name: string;
  session_type: 'meal-planner' | 'kitchen';
  room_name?: string;  // Optional - LiveKit remnant
  ingredients?: ChatIngredient[];
  created_at: string;
  updated_at: string;
}

export interface MealPlannerSessionWithMessages extends MealPlannerSession {
  messages: SessionMessage[];
}

export interface SessionMessage {
  role: 'user' | 'assistant';
  content: string | MessageContent;  // Support both plain strings and structured content
  created_at: string;
}

export interface CreateSessionResponse {
  message: string;
  session: MealPlannerSession;
}

export interface ListSessionsResponse {
  sessions: MealPlannerSession[];
  count: number;
}

export interface GetSessionResponse {
  session: MealPlannerSessionWithMessages;
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
