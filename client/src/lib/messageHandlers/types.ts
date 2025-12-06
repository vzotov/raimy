import type { Ingredient } from '@/components/shared/IngredientList';
import type { Timer } from '@/components/shared/TimerList';
import type { ChatAction, ChatState } from './chatTypes';

/**
 * Kitchen-specific state extends base chat state
 */
export interface KitchenMessageState extends ChatState {
  ingredients: Ingredient[];
  timers: Timer[];
}

/**
 * Kitchen-specific actions combined with base chat actions
 */
export type KitchenMessageAction =
  | ChatAction
  | { type: 'SET_INGREDIENTS'; payload: Ingredient[] }
  | { type: 'UPDATE_INGREDIENTS'; payload: Ingredient[] }
  | { type: 'ADD_TIMER'; payload: Timer };
