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

export type SessionNameContent = {
  type: 'session_name';
  name: string;
};

export type RecipeStep = {
  instruction: string;
  duration?: number;
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

/**
 * Recipe update messages from agent MCP tools
 * Three separate actions for bulk updates
 */
export type RecipeMetadataUpdate = {
  type: 'recipe_update';
  action: 'set_metadata';
  name: string;
  description?: string;
  difficulty?: string;
  total_time?: string;
  servings?: number | string;
  tags?: string[];
};

export type RecipeIngredientsUpdate = {
  type: 'recipe_update';
  action: 'set_ingredients';
  ingredients: ChatIngredient[];
};

export type RecipeStepsUpdate = {
  type: 'recipe_update';
  action: 'set_steps';
  steps: RecipeStep[];
};

export type RecipeUpdateContent =
  | RecipeMetadataUpdate
  | RecipeIngredientsUpdate
  | RecipeStepsUpdate;

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
  | SessionNameContent
  | RecipeContent
  | RecipeUpdateContent
  | TimerContent
  | SystemContent;
