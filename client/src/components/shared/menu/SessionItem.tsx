'use client';

import classNames from 'classnames';
import { forwardRef } from 'react';
import type { ChatSession } from '@/types/chat-session';
import SessionItemDisplayMode from './SessionItemDisplayMode';
import SessionItemEditMode from './SessionItemEditMode';

interface SessionItemProps {
  session: ChatSession;
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

const SessionItem = forwardRef<HTMLDivElement, SessionItemProps>(function SessionItem({
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
}, ref) {
  return (
    <div
      ref={ref}
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
          onEdit={onStartEdit}
          onDelete={onDelete}
          onClick={onClick}
        />
      )}
    </div>
  );
});

export default SessionItem;
