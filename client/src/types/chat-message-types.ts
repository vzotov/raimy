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

/**
 * Unified recipe update type - handles both full recipe and incremental updates
 * Used in meal planner for live recipe editing
 */
export type RecipeUpdateContent = {
  type: 'recipe_update';
  action:
    | 'set'
    | 'update_metadata'
    | 'set_metadata' // NEW: Replace all metadata
    | 'set_ingredients' // NEW: Replace all ingredients
    | 'set_steps' // NEW: Replace all steps
    | 'add_ingredient'
    | 'remove_ingredient'
    | 'update_ingredient'
    | 'add_step'
    | 'remove_step'
    | 'update_step';
  recipe_id?: string;
  // Full recipe fields (for 'set' action) - all optional
  name?: string;
  description?: string;
  difficulty?: string;
  total_time_minutes?: number; // Keep for backward compat
  total_time?: string; // NEW: String-based time
  servings?: number | string; // Support both for backward compat
  tags?: string[];
  ingredients?: ChatIngredient[];
  steps?: RecipeStep[] | string[]; // NEW: Support simple string steps
  // Incremental update fields (for other actions)
  ingredient?: ChatIngredient;
  ingredient_index?: number;
  step?: RecipeStep;
  step_number?: number;
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
  | RecipeUpdateContent
  | TimerContent
  | SystemContent;
