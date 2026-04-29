'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useChatSessions } from '@/hooks/useSessions';
import ConfirmDialog from '@/components/shared/ConfirmDialog';
import SectionHeader from './SectionHeader';
import SessionList from './SessionList';

interface ChatMenuSectionProps {
  onMenuClose: () => void;
}

export default function ChatMenuSection({ onMenuClose }: ChatMenuSectionProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);
  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);

  const { sessions, updateSessionName, deleteSession } = useChatSessions();

  useEffect(() => {
    if (pathname.startsWith('/chat')) {
      setIsExpanded(true);
    }
  }, [pathname]);

  const handleNewChat = () => {
    router.push('/chat/new');
    onMenuClose();
  };

  const handleDelete = (sessionId: string) => {
    setDeleteSessionId(sessionId);
  };

  const confirmDelete = async () => {
    if (!deleteSessionId) return;
    try {
      await deleteSession(deleteSessionId);
      if (pathname === `/chat/${deleteSessionId}`) {
        router.push('/');
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/chat/${sessionId}`);
    onMenuClose();
  };

  return (
    <div>
      <SectionHeader
        title="Chats"
        isExpanded={isExpanded}
        onToggle={() => setIsExpanded(!isExpanded)}
      />

      {isExpanded && (
        <div className="mt-1 ml-4 space-y-1">
          <button
            onClick={handleNewChat}
            className="w-full text-left px-4 py-2 text-sm font-medium text-text/80 hover:text-primary hover:bg-accent/20 rounded-lg transition-colors duration-150"
          >
            + New Chat
          </button>

          <SessionList
            sessions={sessions}
            currentPath={pathname}
            sessionType="chat"
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
        title="Delete chat"
        description="Are you sure you want to delete this chat? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </div>
  );
}
