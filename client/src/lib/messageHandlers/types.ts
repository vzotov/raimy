import type { Ingredient } from '@/components/shared/IngredientList';
import type { Timer } from '@/components/shared/TimerList';
import type { ChatMessage } from '@/hooks/useChatMessages';

export interface KitchenMessageState {
  messages: ChatMessage[];
  ingredients: Ingredient[];
  timers: Timer[];
  recipeName: string;
  agentStatus: string | null;
}

export type KitchenMessageAction =
  | {
      type: 'ADD_OR_UPDATE_MESSAGE';
      payload: Omit<ChatMessage, 'timestamp'>;
    }
  | { type: 'SET_INGREDIENTS'; payload: Ingredient[] }
  | { type: 'UPDATE_INGREDIENTS'; payload: Ingredient[] }
  | { type: 'ADD_TIMER'; payload: Timer }
  | { type: 'SET_RECIPE_NAME'; payload: string }
  | { type: 'SET_AGENT_STATUS'; payload: string | null }
  | { type: 'RESET_AGENT_STATUS' };
