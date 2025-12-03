'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useKitchenSessions } from '@/hooks/useSessions';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface KitchenMenuSectionProps {
  onMenuClose: () => void;
}

export default function KitchenMenuSection({ onMenuClose }: KitchenMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    sessions: kitchenSessions,
    updateSessionName,
    deleteSession,
    createSession,
  } = useKitchenSessions();

  // Auto-expand when on a kitchen page
  useEffect(() => {
    if (pathname.startsWith('/kitchen')) {
      setIsExpanded(true);
    }
  }, [pathname]);

  const handleStartCooking = async () => {
    try {
      const session = await createSession();

      if (session?.id) {
        router.push(`/kitchen/${session.id}`);
        onMenuClose();
      }
    } catch (err) {
      console.error('Error creating kitchen session:', err);
    }
  };

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      await deleteSession(sessionId);
      if (pathname === `/kitchen/${sessionId}`) {
        router.push('/kitchen');
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/kitchen/${sessionId}`);
    onMenuClose();
  };

  return (
    <div>
      <SectionHeader
        title="Kitchen"
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />

      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1">
          <button
            onClick={handleStartCooking}
            className="w-full text-left px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
          >
            + Start Cooking
          </button>

          <SessionList
            sessions={kitchenSessions}
            currentPath={pathname}
            sessionType="kitchen"
            onUpdateSessionName={updateSessionName}
            onDelete={handleDelete}
            onSessionClick={handleSessionClick}
          />
        </div>
      )}
    </div>
  );
}