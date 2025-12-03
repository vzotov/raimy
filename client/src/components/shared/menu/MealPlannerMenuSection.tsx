'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useMealPlannerSessions } from '@/hooks/useSessions';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface MealPlannerMenuSectionProps {
  onMenuClose: () => void;
}

export default function MealPlannerMenuSection({ onMenuClose }: MealPlannerMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    sessions,
    updateSessionName,
    deleteSession,
  } = useMealPlannerSessions();

  // Auto-expand when on a meal planner page
  useEffect(() => {
    if (pathname.startsWith('/meal-planner')) {
      setIsExpanded(true);
    }
  }, [pathname]);

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
        title="Meal Planner"
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />

      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1">
          <Link
            href="/meal-planner"
            className="block px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
            onClick={onMenuClose}
          >
            + New Meal Plan
          </Link>

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