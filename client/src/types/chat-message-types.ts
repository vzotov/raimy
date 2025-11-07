/**
 * Type definitions for structured chat messages in the meal planner.
 * Supports multiple message types with type-safe content.
 */

import { BaseIngredient } from './ingredient';

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
};

// Union type for all message content types
export type MessageContent =
  | TextContent
  | IngredientsContent;
