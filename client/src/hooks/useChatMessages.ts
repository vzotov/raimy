/**
 * Chat message types
 *
 * This file contains type definitions for chat messages used throughout the application.
 */

import { MessageContent } from '@/types/chat-message-types';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string | MessageContent;
  timestamp: Date;
  id: string;
}
