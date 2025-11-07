import { useState, useEffect, useCallback } from 'react';
import { mealPlannerSessions } from '@/lib/api';
import type { MealPlannerSession } from '@/types/meal-planner-session';

export function useMealPlannerSessions() {
  const [sessions, setSessions] = useState<MealPlannerSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlannerSessions.list();

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        setSessions(response.data.sessions);
      }
    } catch (err) {
      setError('Failed to fetch sessions');
      console.error('Error fetching sessions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createSession = useCallback(async () => {
    try {
      const response = await mealPlannerSessions.create();

      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        // Add to local state optimistically
        setSessions(prev => [response.data!.session, ...prev]);
        return response.data.session;
      }
    } catch (err) {
      console.error('Error creating session:', err);
      throw err;
    }
  }, []);

  const updateSessionName = useCallback(async (sessionId: string, newName: string) => {
    try {
      const response = await mealPlannerSessions.updateName(sessionId, {
        session_name: newName,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      // Update local state
      setSessions(prev =>
        prev.map(session =>
          session.id === sessionId
            ? { ...session, session_name: newName }
            : session
        )
      );

      return response.data;
    } catch (err) {
      console.error('Error updating session name:', err);
      throw err;
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      const response = await mealPlannerSessions.delete(sessionId);

      if (response.error) {
        throw new Error(response.error);
      }

      // Remove from local state
      setSessions(prev => prev.filter(session => session.id !== sessionId));

      return response.data;
    } catch (err) {
      console.error('Error deleting session:', err);
      throw err;
    }
  }, []);

  // Handle real-time updates from SSE
  const handleSessionCreated = useCallback((newSession: MealPlannerSession) => {
    setSessions(prev => {
      // Check if already exists to avoid duplicates
      if (prev.some(s => s.id === newSession.id)) {
        return prev;
      }
      return [newSession, ...prev];
    });
  }, []);

  const handleSessionNameUpdated = useCallback((data: { id: string; session_name: string }) => {
    setSessions(prev =>
      prev.map(session =>
        session.id === data.id
          ? { ...session, session_name: data.session_name }
          : session
      )
    );
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return {
    sessions,
    loading,
    error,
    createSession,
    updateSessionName,
    deleteSession,
    refetch: fetchSessions,
    // For SSE integration
    handleSessionCreated,
    handleSessionNameUpdated,
  };
}
