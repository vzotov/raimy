'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useRecipeCreatorSessions } from '@/hooks/useSessions';
import ConfirmDialog from '@/components/shared/ConfirmDialog';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface RecipeCreatorMenuSectionProps {
  onMenuClose: () => void;
}

export default function RecipeCreatorMenuSection({
  onMenuClose,
}: RecipeCreatorMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);
  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);

  const { sessions, updateSessionName, deleteSession } =
    useRecipeCreatorSessions();

  // Auto-expand when on a recipe creator page
  useEffect(() => {
    if (pathname.startsWith('/recipe-creator')) {
      setIsExpanded(true);
    }
  }, [pathname]);

  const handleCreateRecipe = () => {
    router.push('/recipe-creator/new');
    onMenuClose();
  };

  const handleDelete = (sessionId: string) => {
    setDeleteSessionId(sessionId);
  };

  const confirmDelete = async () => {
    if (!deleteSessionId) return;

    try {
      await deleteSession(deleteSessionId);
      if (pathname === `/recipe-creator/${deleteSessionId}`) {
        router.push('/recipe-creator');
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/recipe-creator/${sessionId}`);
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
            className="w-full rounded-lg px-4 py-2 text-left text-sm font-medium text-text/80 transition-colors duration-150 hover:bg-accent/20 hover:text-primary"
          >
            + New Recipe
          </button>

          <SessionList
            sessions={sessions}
            currentPath={pathname}
            sessionType="recipe-creator"
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
