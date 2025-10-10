/**
 * Type definitions for structured chat messages in the meal planner.
 * Supports multiple message types with type-safe content.
 */

// Base ingredient structure
export interface Ingredient {
  name: string;
  quantity?: number;
  unit?: string;
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
  items: Ingredient[];
};

// Union type for all message content types
export type MessageContent =
  | TextContent
  | IngredientsContent;

// Extended chat message with typed content
export interface TypedChatMessage {
  role: 'user' | 'assistant';
  messageContent: MessageContent;
  timestamp: Date;
  id: string;
}

// Type guard functions
export function isTextContent(content: MessageContent): content is TextContent {
  return content.type === 'text';
}

export function isIngredientsContent(content: MessageContent): content is IngredientsContent {
  return content.type === 'ingredients';
}
