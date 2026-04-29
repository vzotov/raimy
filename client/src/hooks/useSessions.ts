import useSWR, { mutate } from 'swr';
import { chatSessions } from '@/lib/api';
import type { ChatSession } from '@/types/chat-session';

export const SESSIONS_KEYS = {
  chat: '/api/chat-sessions?type=chat',
} as const;

/**
 * Hook for managing unified chat sessions
 */
export function useChatSessions() {
  const swrKey = SESSIONS_KEYS.chat;

  const {
    data,
    error,
    isLoading,
    mutate: revalidate,
  } = useSWR(
    swrKey,
    async () => {
      const response = await chatSessions.list('chat');
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data?.sessions || [];
    },
    {
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      keepPreviousData: true,
    },
  );

  const createSession = async (recipeId?: string) => {
    const response = await chatSessions.create('chat', recipeId);
    if (response.error) {
      throw new Error(response.error);
    }

    if (response.data) {
      await mutate(
        swrKey,
        (current: ChatSession[] = []) => [response.data!.session, ...current],
        false,
      );
      revalidate();
      return response.data.session;
    }
  };

  const updateSessionName = async (sessionId: string, newName: string) => {
    const response = await chatSessions.updateName(sessionId, {
      session_name: newName,
    });

    if (response.error) {
      throw new Error(response.error);
    }

    await mutate(
      swrKey,
      (current: ChatSession[] = []) =>
        current.map((session) =>
          session.id === sessionId
            ? { ...session, session_name: newName }
            : session,
        ),
      false,
    );

    return response.data;
  };

  const deleteSession = async (sessionId: string) => {
    const response = await chatSessions.delete(sessionId);
    if (response.error) {
      throw new Error(response.error);
    }

    await mutate(
      swrKey,
      (current: ChatSession[] = []) =>
        current.filter((session) => session.id !== sessionId),
      false,
    );

    return response.data;
  };

  return {
    sessions: data || [],
    loading: isLoading,
    error: error?.message || null,
    createSession,
    updateSessionName,
    deleteSession,
    refetch: revalidate,
  };
}

/**
 * Helper to update session name in cache from anywhere (e.g., chat components)
 */
export function updateSessionNameInCache(
  sessionId: string,
  sessionName: string,
  sessionType: 'chat',
) {
  void sessionType; // always 'chat' now
  mutate(
    SESSIONS_KEYS.chat,
    (current: ChatSession[] = []) =>
      current.map((session) =>
        session.id === sessionId
          ? { ...session, session_name: sessionName }
          : session,
      ),
    false,
  );
}
