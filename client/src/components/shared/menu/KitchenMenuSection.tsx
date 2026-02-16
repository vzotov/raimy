'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useKitchenSessions } from '@/hooks/useSessions';
import ConfirmDialog from '@/components/shared/ConfirmDialog';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface KitchenMenuSectionProps {
  onMenuClose: () => void;
}

export default function KitchenMenuSection({
  onMenuClose,
}: KitchenMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);
  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);

  const {
    sessions: kitchenSessions,
    updateSessionName,
    deleteSession,
  } = useKitchenSessions();

  // Auto-expand when on a kitchen page
  useEffect(() => {
    if (pathname.startsWith('/kitchen')) {
      setIsExpanded(true);
    }
  }, [pathname]);

  const handleStartCooking = () => {
    router.push('/kitchen/new');
    onMenuClose();
  };

  const handleDelete = (sessionId: string) => {
    setDeleteSessionId(sessionId);
  };

  const confirmDelete = async () => {
    if (!deleteSessionId) return;

    try {
      await deleteSession(deleteSessionId);
      if (pathname === `/kitchen/${deleteSessionId}`) {
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

      <ConfirmDialog
        open={deleteSessionId !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteSessionId(null);
        }}
        title="Delete session"
        description="Are you sure you want to delete this session? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </div>
  );
}
