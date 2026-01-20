/**
 * Type definitions for structured chat messages in the meal planner.
 * Supports multiple message types with type-safe content.
 */

import type { RecipeIngredient, RecipeNutrition, RecipeStep } from './recipe';

// Message content variants
export type TextContent = {
  type: 'text';
  content: string;
};

export type KitchenStepContent = {
  type: 'kitchen-step';
  content: string;
};

export type IngredientsContent = {
  type: 'ingredients';
  title?: string;
  items: RecipeIngredient[];
  action: 'set' | 'update';
};

export type SessionNameContent = {
  type: 'session_name';
  name: string;
};

export type RecipeContent = {
  type: 'recipe';
  recipe_id: string;
  name: string;
  description?: string;
  ingredients: RecipeIngredient[];
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
  ingredients: RecipeIngredient[];
};

export type RecipeStepsUpdate = {
  type: 'recipe_update';
  action: 'set_steps';
  steps: RecipeStep[];
};

export type RecipeNutritionUpdate = {
  type: 'recipe_update';
  action: 'set_nutrition';
  nutrition: RecipeNutrition;
};

export type RecipeUpdateContent =
  | RecipeMetadataUpdate
  | RecipeIngredientsUpdate
  | RecipeStepsUpdate
  | RecipeNutritionUpdate;

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
  | KitchenStepContent
  | IngredientsContent
  | SessionNameContent
  | RecipeContent
  | RecipeUpdateContent
  | TimerContent
  | SystemContent;
