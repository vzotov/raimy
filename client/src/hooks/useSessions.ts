import useSWR, { mutate } from 'swr';
import {
  kitchenSessions as kitchenSessionsApi,
  mealPlannerSessions,
} from '@/lib/api';
import type { MealPlannerSession } from '@/types/meal-planner-session';

// SWR keys for caching
export const SESSIONS_KEYS = {
  mealPlanner: '/api/meal-planner-sessions?type=meal-planner',
  kitchen: '/api/meal-planner-sessions?type=kitchen',
} as const;

/**
 * Hook for managing meal planner sessions with SWR
 */
export function useMealPlannerSessions() {
  const {
    data,
    error,
    isLoading,
    mutate: revalidate,
  } = useSWR(
    SESSIONS_KEYS.mealPlanner,
    async () => {
      const response = await mealPlannerSessions.list('meal-planner');
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data?.sessions || [];
    },
    {
      // Revalidate on focus and reconnect for fresh data
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      // Keep previous data while revalidating
      keepPreviousData: true,
    },
  );

  const createSession = async () => {
    const response = await mealPlannerSessions.create();
    if (response.error) {
      throw new Error(response.error);
    }

    if (response.data) {
      // Optimistically update cache
      await mutate(
        SESSIONS_KEYS.mealPlanner,
        (current: MealPlannerSession[] = []) => [
          response.data!.session,
          ...current,
        ],
        false,
      );
      // Revalidate to ensure consistency
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

    // Optimistically update cache
    await mutate(
      SESSIONS_KEYS.mealPlanner,
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

    // Optimistically update cache
    await mutate(
      SESSIONS_KEYS.mealPlanner,
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
 * Hook for managing kitchen sessions with SWR
 */
export function useKitchenSessions() {
  const {
    data,
    error,
    isLoading,
    mutate: revalidate,
  } = useSWR(
    SESSIONS_KEYS.kitchen,
    async () => {
      const response = await kitchenSessionsApi.list();
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

  const createSession = async () => {
    const response = await kitchenSessionsApi.create();
    if (response.error) {
      throw new Error(response.error);
    }

    if (response.data) {
      // Optimistically update cache
      await mutate(
        SESSIONS_KEYS.kitchen,
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
    const response = await kitchenSessionsApi.updateName(sessionId, {
      session_name: newName,
    });

    if (response.error) {
      throw new Error(response.error);
    }

    // Optimistically update cache
    await mutate(
      SESSIONS_KEYS.kitchen,
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
    const response = await kitchenSessionsApi.delete(sessionId);
    if (response.error) {
      throw new Error(response.error);
    }

    // Optimistically update cache
    await mutate(
      SESSIONS_KEYS.kitchen,
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
