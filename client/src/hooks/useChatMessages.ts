/**
 * Chat message types
 *
 * This file contains type definitions for chat messages used throughout the application.
 */

import type { MessageContent } from '@/types/chat-message-types';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: MessageContent;
  timestamp: Date;
  id: string;
}
