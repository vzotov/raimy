'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useMealPlannerSessions } from '@/hooks/useSessions';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface MealPlannerMenuSectionProps {
  onMenuClose: () => void;
}

export default function MealPlannerMenuSection({
  onMenuClose,
}: MealPlannerMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  const { sessions, updateSessionName, deleteSession, createSession } =
    useMealPlannerSessions();

  // Auto-expand when on a meal planner page
  useEffect(() => {
    if (pathname.startsWith('/meal-planner')) {
      setIsExpanded(true);
    }
  }, [pathname]);

  const handleCreateRecipe = async () => {
    try {
      const session = await createSession();

      if (session?.id) {
        router.push(`/meal-planner/${session.id}`);
        onMenuClose();
      }
    } catch (err) {
      console.error('Error creating meal planner session:', err);
    }
  };

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      await deleteSession(sessionId);
      if (pathname === `/meal-planner/${sessionId}`) {
        router.push('/meal-planner');
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/meal-planner/${sessionId}`);
    onMenuClose();
  };

  return (
    <div>
      <SectionHeader
        title="Recipe Creator"
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />

      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1">
          <button
            onClick={handleCreateRecipe}
            className="w-full text-left px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
          >
            + New Recipe
          </button>

          <SessionList
            sessions={sessions}
            currentPath={pathname}
            sessionType="meal-planner"
            onUpdateSessionName={updateSessionName}
            onDelete={handleDelete}
            onSessionClick={handleSessionClick}
          />
        </div>
      )}
    </div>
  );
}
