'use client';

import type { ChatSession } from '@/types/chat-session';
import EditIcon from '@/components/icons/EditIcon';
import TrashIcon from '@/components/icons/TrashIcon';

interface SessionItemDisplayModeProps {
  session: ChatSession;
  onEdit: (e: React.MouseEvent) => void;
  onDelete: (e: React.MouseEvent) => void;
  onClick: () => void;
}

export default function SessionItemDisplayMode({
  session,
  onEdit,
  onDelete,
  onClick,
}: SessionItemDisplayModeProps) {
  return (
    <div
      onClick={onClick}
      className="w-full text-left px-3 py-2 flex items-center justify-between cursor-pointer"
    >
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-text truncate">
          {session.session_name}
        </div>
      </div>

      {/* Actions (always visible on mobile, hover on desktop) */}
      <div className="opacity-100 sm:opacity-0 sm:group-hover:opacity-100 flex items-center gap-1 ml-2 transition-opacity">
        <button
          onClick={onEdit}
          className="p-1 text-xs text-text/50 hover:text-primary rounded transition-colors"
          title="Rename"
        >
          <EditIcon className="w-4 h-4" />
        </button>
        <button
          onClick={onDelete}
          className="p-1 text-xs text-text/50 hover:text-red-500 rounded transition-colors"
          title="Delete"
        >
          <TrashIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
