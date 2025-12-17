import useSWR, { mutate } from 'swr';
import { chatSessions } from '@/lib/api';
import type { ChatSession } from '@/types/chat-session';

// SWR keys for caching
export const SESSIONS_KEYS = {
  recipeCreator: '/api/chat-sessions?type=recipe-creator',
  kitchen: '/api/chat-sessions?type=kitchen',
} as const;

type SessionType = 'recipe-creator' | 'kitchen';

/**
 * Generic hook for managing sessions with SWR
 */
function useSessions(sessionType: SessionType) {
  const swrKey =
    sessionType === 'kitchen'
      ? SESSIONS_KEYS.kitchen
      : SESSIONS_KEYS.recipeCreator;

  const {
    data,
    error,
    isLoading,
    mutate: revalidate,
  } = useSWR(
    swrKey,
    async () => {
      const response = await chatSessions.list(sessionType);
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
    const response = await chatSessions.create(sessionType, recipeId);
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
 * Hook for managing recipe creator sessions
 */
export function useRecipeCreatorSessions() {
  return useSessions('recipe-creator');
}

/**
 * Hook for managing kitchen sessions
 */
export function useKitchenSessions() {
  return useSessions('kitchen');
}

/**
 * Helper to update session name in cache from anywhere (e.g., chat components)
 */
export function updateSessionNameInCache(
  sessionId: string,
  sessionName: string,
  sessionType: 'recipe-creator' | 'kitchen',
) {
  const key =
    sessionType === 'kitchen'
      ? SESSIONS_KEYS.kitchen
      : SESSIONS_KEYS.recipeCreator;

  mutate(
    key,
    (current: ChatSession[] = []) =>
      current.map((session) =>
        session.id === sessionId
          ? { ...session, session_name: sessionName }
          : session,
      ),
    false,
  );
}
