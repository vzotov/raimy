'use client';

import classNames from 'classnames';
import type { MealPlannerSession } from '@/types/meal-planner-session';
import SessionItemDisplayMode from './SessionItemDisplayMode';
import SessionItemEditMode from './SessionItemEditMode';

interface SessionItemProps {
  session: MealPlannerSession;
  isActive: boolean;
  isEditing: boolean;
  editValue: string;
  onEditValueChange: (value: string) => void;
  onStartEdit: (e: React.MouseEvent) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onClick: () => void;
}

export default function SessionItem({
  session,
  isActive,
  isEditing,
  editValue,
  onEditValueChange,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
  onClick,
}: SessionItemProps) {
  return (
    <div
      key={session.id}
      className={classNames('group relative rounded-lg transition-colors', {
        'bg-accent/30': isActive,
        'hover:bg-accent/10': !isActive && !isEditing,
      })}
    >
      {isEditing ? (
        <SessionItemEditMode
          value={editValue}
          onChange={onEditValueChange}
          onSave={onSaveEdit}
          onCancel={onCancelEdit}
        />
      ) : (
        <SessionItemDisplayMode
          session={session}
          isActive={isActive}
          onEdit={onStartEdit}
          onDelete={onDelete}
          onClick={onClick}
        />
      )}
    </div>
  );
}
