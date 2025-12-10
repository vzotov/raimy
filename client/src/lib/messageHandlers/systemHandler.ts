import type { Dispatch } from 'react';
import type { SystemContent } from '@/types/chat-message-types';
import type { ChatAction } from './chatTypes';

export function handleSystemMessage(
  content: SystemContent,
  dispatch: Dispatch<ChatAction>,
): void {
  switch (content.type) {
    case 'connected':
      console.log('✅', content.message);
      break;

    case 'thinking':
      // Set agent status to show thinking indicator
      dispatch({ type: 'SET_AGENT_STATUS', payload: content.message });
      break;

    case 'error':
      console.error('❌', content.message);
      dispatch({ type: 'RESET_AGENT_STATUS' });
      break;
  }
}
