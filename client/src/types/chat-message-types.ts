/**
 * Type definitions for structured chat messages in the meal planner.
 * Supports multiple message types with type-safe content.
 */

import type { BaseIngredient } from './ingredient';

/**
 * Chat ingredient extends base with additional meal planning fields
 */
export interface ChatIngredient extends BaseIngredient {
  notes?: string;
}

// Message content variants
export type TextContent = {
  type: 'text';
  content: string;
};

export type IngredientsContent = {
  type: 'ingredients';
  title?: string;
  items: ChatIngredient[];
  action: 'set' | 'update';
};

export type RecipeNameContent = {
  type: 'recipe_name';
  name: string;
};

export type RecipeStep = {
  step_number: number;
  instruction: string;
  duration_minutes?: number;
  ingredients?: string[];
};

export type RecipeContent = {
  type: 'recipe';
  recipe_id: string;
  name: string;
  description?: string;
  ingredients: ChatIngredient[];
  steps: RecipeStep[];
  total_time_minutes?: number;
  difficulty?: string;
  servings?: number;
  tags?: string[];
};

export type TimerContent = {
  type: 'timer';
  duration: number;
  label: string;
  started_at: number;
};

export type SystemContent = {
  type: 'connected' | 'error' | 'thinking';
  message: string;
};

// Union type for all message content types
export type MessageContent =
  | TextContent
  | IngredientsContent
  | RecipeNameContent
  | RecipeContent
  | TimerContent
  | SystemContent;
