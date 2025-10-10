'use client';

import { useEffect } from 'react';
import { useConnectionState, useParticipants } from '@livekit/components-react';
import Chat from '@/components/shared/chat/Chat';
import classNames from 'classnames';

export default function MealPlanner() {
  const connectionState = useConnectionState();
  const participants = useParticipants();

  // Debug logging
  useEffect(() => {
    console.log('[MealPlanner] Connection state:', connectionState);
  }, [connectionState]);

  useEffect(() => {
    console.log('[MealPlanner] Participants:', participants);
    participants.forEach((p, idx) => {
      console.log(`[MealPlanner] Participant ${idx}:`, {
        identity: p.identity,
        name: p.name,
        isSpeaking: p.isSpeaking,
        metadata: p.metadata,
      });
    });
  }, [participants]);

  return (
    <div className={classNames('flex flex-1 flex-col w-full max-w-4xl mx-auto')}>
      {/* Header */}
      <div className="p-4 border-b border-accent/20">
        <h1 className="text-2xl font-bold text-text">Meal Planner</h1>
        <p className="text-sm text-text/70 mt-1">
          Plan your meals with AI assistance
        </p>
        {connectionState !== 'connected' && (
          <p className="text-xs text-primary mt-2">Connecting to assistant...</p>
        )}
        {connectionState === 'connected' && (
          <p className="text-xs text-green-500 mt-2">
            Connected • {participants.length} participant(s)
          </p>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Chat />
      </div>
    </div>
  );
}
