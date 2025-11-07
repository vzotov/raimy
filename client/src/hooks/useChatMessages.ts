import { useMemo, useEffect } from 'react';
import { useChat, useLocalParticipant, useTranscriptions } from '@livekit/components-react';
import { useAgentParticipant } from './useAgentParticipant';
import { MessageContent } from '@/types/chat-message-types';
import { parseMessageContent } from '@/utils/messageParser';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string | MessageContent;
  timestamp: Date;
  id: string;
}

/**
 * Custom hook to convert LiveKit messages into our ChatMessage format.
 * Combines chat messages (from user) and transcriptions (from agent).
 *
 * @returns Array of chat messages with role, content, and timestamp
 */
export function useChatMessages(): ChatMessage[] {
  const { chatMessages } = useChat();
  const { localParticipant } = useLocalParticipant();
  const agent = useAgentParticipant();
  const transcriptions = useTranscriptions();

  // Debug logging
  useEffect(() => {
    console.log('[useChatMessages] localParticipant:', localParticipant?.identity);
    console.log('[useChatMessages] agent:', agent?.identity);
    console.log('[useChatMessages] chatMessages count:', chatMessages?.length);
    console.log('[useChatMessages] chatMessages:', chatMessages);
    console.log('[useChatMessages] transcriptions count:', transcriptions?.length);
    console.log('[useChatMessages] transcriptions:', transcriptions);
  }, [localParticipant, agent, chatMessages, transcriptions]);

  const messages = useMemo(() => {
    if (!localParticipant) {
      return [];
    }

    const allMessages: ChatMessage[] = [];

    // Add user chat messages
    chatMessages.forEach((msg) => {
      const isFromLocalUser = msg.from?.identity === localParticipant.identity;

      allMessages.push({
        role: isFromLocalUser ? 'user' : 'assistant',
        content: msg.message,
        timestamp: new Date(msg.timestamp),
        id: `chat-${msg.from?.identity}-${msg.timestamp}`,
      });
    });

    // Add agent transcriptions (text responses from agent)
    if (agent) {
      transcriptions.forEach((transcription) => {
        const isFromAgent = transcription.participantInfo?.identity === agent.identity;
        if (isFromAgent && transcription.text) {
          const timestamp = transcription.streamInfo.timestamp;

          console.log('[useChatMessages] Converted timestamp:', timestamp, 'Date:', new Date(timestamp));

          // Parse message content - handles both plain text and structured JSON
          const parsedContent = parseMessageContent(transcription.text);

          allMessages.push({
            role: 'assistant',
            content: parsedContent,
            timestamp: new Date(timestamp),
            id: `transcription-${transcription.participantInfo?.identity}-${timestamp}`,
          });
        }
      });
    }

    // Sort by timestamp
    allMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    return allMessages;
  }, [chatMessages, transcriptions, localParticipant, agent]);

  return messages;
}
