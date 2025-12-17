import useSWR, { mutate } from 'swr';
import { mealPlannerSessions } from '@/lib/api';
import type { MealPlannerSession } from '@/types/meal-planner-session';

// SWR keys for caching
export const SESSIONS_KEYS = {
  mealPlanner: '/api/meal-planner-sessions?type=meal-planner',
  kitchen: '/api/meal-planner-sessions?type=kitchen',
} as const;

type SessionType = 'meal-planner' | 'kitchen';

/**
 * Generic hook for managing sessions with SWR
 */
function useSessions(sessionType: SessionType) {
  const swrKey = sessionType === 'kitchen' ? SESSIONS_KEYS.kitchen : SESSIONS_KEYS.mealPlanner;

  const {
    data,
    error,
    isLoading,
    mutate: revalidate,
  } = useSWR(
    swrKey,
    async () => {
      const response = await mealPlannerSessions.list(sessionType);
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
    const response = await mealPlannerSessions.create(sessionType, recipeId);
    if (response.error) {
      throw new Error(response.error);
    }

    if (response.data) {
      await mutate(
        swrKey,
        (current: MealPlannerSession[] = []) => [
          response.data!.session,
          ...current,
        ],
        false,
      );
      revalidate();
      return response.data.session;
    }
  };

  const updateSessionName = async (sessionId: string, newName: string) => {
    const response = await mealPlannerSessions.updateName(sessionId, {
      session_name: newName,
    });

    if (response.error) {
      throw new Error(response.error);
    }

    await mutate(
      swrKey,
      (current: MealPlannerSession[] = []) =>
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
    const response = await mealPlannerSessions.delete(sessionId);
    if (response.error) {
      throw new Error(response.error);
    }

    await mutate(
      swrKey,
      (current: MealPlannerSession[] = []) =>
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
 * Hook for managing meal planner sessions
 */
export function useMealPlannerSessions() {
  return useSessions('meal-planner');
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
  sessionType: 'meal-planner' | 'kitchen',
) {
  const key =
    sessionType === 'kitchen'
      ? SESSIONS_KEYS.kitchen
      : SESSIONS_KEYS.mealPlanner;

  mutate(
    key,
    (current: MealPlannerSession[] = []) =>
      current.map((session) =>
        session.id === sessionId
          ? { ...session, session_name: sessionName }
          : session,
      ),
    false,
  );
}
