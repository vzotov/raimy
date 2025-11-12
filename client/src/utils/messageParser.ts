import { MessageContent } from '@/types/chat-message-types';

/**
 * Parses LLM output into structured MessageContent.
 * Supports both plain text and JSON-formatted structured messages.
 *
 * Expected JSON format from LLM:
 * {
 *   "type": "ingredients",
 *   "title": "Shopping List",
 *   "items": [...]
 * }
 */
export function parseMessageContent(rawContent: string): MessageContent {
  // Try to parse as JSON first
  const trimmed = rawContent.trim();

  // Check if it looks like JSON
  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) ||
      (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      const parsed = JSON.parse(trimmed);

      // Validate it has a type field
      if (parsed && typeof parsed === 'object' && 'type' in parsed) {
        // Type validation - ensure it matches our MessageContent union
        if (isValidMessageContent(parsed)) {
          return parsed as MessageContent;
        }
      }
    } catch (e) {
      // Not valid JSON, fall through to text
      console.warn('[messageParser] Failed to parse JSON, treating as text:', e);
    }
  }

  // Check for JSON embedded in markdown code blocks
  const jsonBlockMatch = trimmed.match(/```(?:json)?\s*\n([\s\S]+?)\n```/);
  if (jsonBlockMatch) {
    try {
      const parsed = JSON.parse(jsonBlockMatch[1]);
      if (parsed && typeof parsed === 'object' && 'type' in parsed && isValidMessageContent(parsed)) {
        return parsed as MessageContent;
      }
    } catch (e) {
      console.warn('[messageParser] Failed to parse JSON from code block:', e);
    }
  }

  // Default to text message
  return {
    type: 'text',
    content: rawContent,
  };
}

/**
 * Type guard to validate MessageContent structure at runtime
 */
function isValidMessageContent(obj: unknown): boolean {
  if (!obj || typeof obj !== 'object' || !('type' in obj)) {
    return false;
  }

  const typed = obj as { type: string; [key: string]: unknown };

  switch (typed.type) {
    case 'text':
      return 'content' in typed && typeof typed.content === 'string';

    case 'ingredients':
      return (
        'items' in typed &&
        Array.isArray(typed.items) &&
        typed.items.every((item: unknown) =>
          typeof item === 'object' &&
          item !== null &&
          'name' in item &&
          typeof item.name === 'string'
        )
      );

    default:
      return false;
  }
}

/**
 * Helper to detect if a message looks like it might be structured content
 */
export function looksLikeStructuredContent(content: string): boolean {
  const trimmed = content.trim();
  return (
    trimmed.startsWith('{') ||
    trimmed.startsWith('[') ||
    trimmed.includes('```json') ||
    trimmed.includes('"type":')
  );
}
