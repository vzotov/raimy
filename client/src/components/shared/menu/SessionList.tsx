'use client';

import { useState } from 'react';
import { MealPlannerSession } from '@/types/meal-planner-session';
import SessionItem from './SessionItem';

interface SessionListProps {
  sessions: MealPlannerSession[];
  currentPath: string;
  sessionType: 'meal-planner' | 'kitchen';
  onUpdateSessionName: (sessionId: string, newName: string) => Promise<any>;
  onDelete: (sessionId: string) => void;
  onSessionClick: (sessionId: string, sessionType: 'meal-planner' | 'kitchen') => void;
}

export default function SessionList({
  sessions,
  currentPath,
  sessionType,
  onUpdateSessionName,
  onDelete,
  onSessionClick,
}: SessionListProps) {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleStartEdit = (sessionId: string, sessionName: string) => {
    setEditingSessionId(sessionId);
    setEditValue(sessionName);
  };

  const handleSaveEdit = async () => {
    if (!editValue.trim() || !editingSessionId) return;

    try {
      await onUpdateSessionName(editingSessionId, editValue.trim());
      setEditingSessionId(null);
      setEditValue('');
    } catch (err) {
      console.error('Failed to update session name:', err);
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditValue('');
  };

  return (
    <>
      {sessions.slice(0, 10).map((session) => {
        const isActive = currentPath === `/${sessionType}/${session.id}`;
        const isEditing = editingSessionId === session.id;

        const handleStartEditClick = (e: React.MouseEvent) => {
          e.stopPropagation();
          handleStartEdit(session.id, session.session_name);
        };

        const handleDeleteClick = (e: React.MouseEvent) => {
          e.stopPropagation();
          onDelete(session.id);
        };

        const handleClick = () => {
          onSessionClick(session.id, sessionType);
        };

        return (
          <SessionItem
            key={session.id}
            session={session}
            isActive={isActive}
            isEditing={isEditing}
            editValue={editValue}
            onEditValueChange={setEditValue}
            onStartEdit={handleStartEditClick}
            onSaveEdit={handleSaveEdit}
            onCancelEdit={handleCancelEdit}
            onDelete={handleDeleteClick}
            onClick={handleClick}
          />
        );
      })}
    </>
  );
}