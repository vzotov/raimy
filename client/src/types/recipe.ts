import type { BaseIngredient } from './ingredient';

/**
 * Recipe ingredient extends base with additional meal planning fields
 */
export interface RecipeIngredient extends BaseIngredient {
  notes?: string;
}

export interface RecipeStep {
  instruction: string;
  duration?: number;
}

export interface Recipe {
  id: string; // Empty string '' for unsaved recipes
  name: string;
  description?: string;
  ingredients?: RecipeIngredient[]; // Optional - may not be set yet during creation
  steps?: RecipeStep[]; // Optional - may not be set yet during creation
  total_time_minutes?: number;
  difficulty?: string;
  servings?: number;
  tags?: string[];
  user_id?: string; // Populated after save
  chat_session_id?: string;
  created_at?: string; // Populated after save
  updated_at?: string; // Populated after save
}
