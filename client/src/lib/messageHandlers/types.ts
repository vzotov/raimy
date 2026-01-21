import type { KitchenIngredient } from '@/components/pages/kitchen/KitchenIngredientList';
import type { Timer } from '@/components/shared/TimerList';
import type { ChatAction, ChatState } from './chatTypes';

/**
 * Kitchen-specific state extends base chat state
 */
export interface KitchenMessageState extends ChatState {
  ingredients: KitchenIngredient[];
  timers: Timer[];
}

/**
 * Kitchen-specific actions combined with base chat actions
 */
export type KitchenMessageAction =
  | ChatAction
  | { type: 'SET_INGREDIENTS'; payload: KitchenIngredient[] }
  | { type: 'UPDATE_INGREDIENTS'; payload: KitchenIngredient[] }
  | { type: 'ADD_TIMER'; payload: Timer };
