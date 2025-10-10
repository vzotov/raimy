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
function isValidMessageContent(obj: any): boolean {
  if (!obj || typeof obj !== 'object' || !obj.type) {
    return false;
  }

  switch (obj.type) {
    case 'text':
      return typeof obj.content === 'string';

    case 'ingredients':
      return (
        Array.isArray(obj.items) &&
        obj.items.every((item: any) =>
          typeof item === 'object' &&
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
