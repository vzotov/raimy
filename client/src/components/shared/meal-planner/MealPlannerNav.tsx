'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useMealPlannerSessions } from '@/hooks/useMealPlannerSessions';
import { useSSE } from '@/hooks/useSSE';
import classNames from 'classnames';
import { MealPlannerSession } from '@/types/meal-planner-session';

export default function MealPlannerNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [isCreating, setIsCreating] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const {
    sessions,
    loading,
    error,
    createSession,
    updateSessionName,
    deleteSession,
    handleSessionCreated,
    handleSessionNameUpdated,
  } = useMealPlannerSessions();

  // Set up SSE for real-time updates
  useSSE({
    onMessage: (event) => {
      if (event.type === 'session_created') {
        const sessionData = event.data as unknown as MealPlannerSession;
        handleSessionCreated(sessionData);
      } else if (event.type === 'session_name_updated') {
        const data = event.data as { id: string; session_name: string };
        handleSessionNameUpdated(data);
      }
    },
  });

  const handleCreateSession = async () => {
    try {
      setIsCreating(true);
      const newSession = await createSession();
      if (newSession) {
        router.push(`/meal-planner/${newSession.id}`);
      }
    } catch (err) {
      console.error('Failed to create session:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleStartEdit = (session: MealPlannerSession) => {
    setEditingSessionId(session.id);
    setEditValue(session.session_name);
  };

  const handleSaveEdit = async (sessionId: string) => {
    if (!editValue.trim()) return;

    try {
      await updateSessionName(sessionId, editValue.trim());
      setEditingSessionId(null);
    } catch (err) {
      console.error('Failed to update session name:', err);
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditValue('');
  };

  const handleDelete = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();

    if (!confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      await deleteSession(sessionId);

      // If we're viewing this session, redirect to meal planner home
      if (pathname === `/meal-planner/${sessionId}`) {
        router.push('/meal-planner');
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    if (editingSessionId === sessionId) return;
    router.push(`/meal-planner/${sessionId}`);
  };

  if (error) {
    return (
      <div className="p-4 text-sm text-red-500">
        Failed to load sessions
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full border-r border-accent/20 bg-background w-64">
      {/* Header */}
      <div className="p-4 border-b border-accent/20">
        <button
          onClick={handleCreateSession}
          disabled={isCreating}
          className={classNames(
            'w-full px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            {
              'bg-primary text-white hover:bg-primary/90': !isCreating,
              'bg-primary/50 text-white/70 cursor-not-allowed': isCreating,
            }
          )}
        >
          {isCreating ? 'Creating...' : '+ New Chat'}
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading && sessions.length === 0 ? (
          <div className="text-center py-8 text-text/50 text-sm">
            Loading sessions...
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 text-text/50 text-sm">
            No sessions yet
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => {
              const isActive = pathname === `/meal-planner/${session.id}`;
              const isEditing = editingSessionId === session.id;

              return (
                <div
                  key={session.id}
                  className={classNames(
                    'group relative rounded-lg transition-colors',
                    {
                      'bg-accent/30': isActive,
                      'hover:bg-accent/10': !isActive && !isEditing,
                    }
                  )}
                >
                  {isEditing ? (
                    <div className="p-2 flex items-center gap-1">
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveEdit(session.id);
                          } else if (e.key === 'Escape') {
                            handleCancelEdit();
                          }
                        }}
                        className="flex-1 px-2 py-1 text-sm bg-background border border-accent/30 rounded focus:outline-none focus:ring-2 focus:ring-primary"
                        autoFocus
                      />
                      <button
                        onClick={() => handleSaveEdit(session.id)}
                        className="px-2 py-1 text-xs text-green-500 hover:text-green-600"
                        title="Save"
                      >
                        ✓
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="px-2 py-1 text-xs text-red-500 hover:text-red-600"
                        title="Cancel"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <div
                      onClick={() => handleSessionClick(session.id)}
                      className="w-full text-left p-3 flex items-start justify-between cursor-pointer"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-text truncate">
                          {session.session_name}
                        </div>
                        <div className="text-xs text-text/50 mt-0.5">
                          {session.message_count || 0} messages
                        </div>
                      </div>

                      {/* Actions (visible on hover) */}
                      <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 ml-2 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartEdit(session);
                          }}
                          className="p-1 text-xs text-text/50 hover:text-primary rounded transition-colors"
                          title="Rename"
                        >
                          ✎
                        </button>
                        <button
                          onClick={(e) => handleDelete(session.id, e)}
                          className="p-1 text-xs text-text/50 hover:text-red-500 rounded transition-colors"
                          title="Delete"
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
