'use client';

import type { MealPlannerSession } from '@/types/meal-planner-session';

interface SessionItemDisplayModeProps {
  session: MealPlannerSession;
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

      {/* Actions (visible on hover) */}
      <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 ml-2 transition-opacity">
        <button
          onClick={onEdit}
          className="p-1 text-xs text-text/50 hover:text-primary rounded transition-colors"
          title="Rename"
        >
          ✎
        </button>
        <button
          onClick={onDelete}
          className="p-1 text-xs text-text/50 hover:text-red-500 rounded transition-colors"
          title="Delete"
        >
          🗑
        </button>
      </div>
    </div>
  );
}
