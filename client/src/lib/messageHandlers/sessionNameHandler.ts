import type { Dispatch } from 'react';
import { updateSessionNameInCache } from '@/hooks/useSessions';
import type { SessionNameContent } from '@/types/chat-message-types';
import type { ChatAction } from './chatTypes';

/**
 * Handle session_name messages - shared across all chat types
 */
export function handleSessionNameMessage(
	content: SessionNameContent,
	dispatch: Dispatch<ChatAction>,
	sessionId: string,
	sessionType: 'meal-planner' | 'kitchen',
): void {
	if (content.name) {
		// Update session name in local state
		dispatch({ type: 'SET_SESSION_NAME', payload: content.name });

		// Update sessions list cache so the sidebar shows updated name
		updateSessionNameInCache(sessionId, content.name, sessionType);
	}
}
