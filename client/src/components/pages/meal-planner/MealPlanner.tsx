'use client';

import { useEffect, useState } from 'react';
import { useConnectionState, useParticipants } from '@livekit/components-react';
import Chat from '@/components/shared/chat/Chat';
import ChatDebugPanel from '@/components/debug/ChatDebugPanel';
import classNames from 'classnames';
import { ChatMessage } from '@/hooks/useChatMessages';
import { MessageContent } from '@/types/chat-message-types';
import { SessionMessage } from '@/types/meal-planner-session';

interface MealPlannerProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
}

export default function MealPlanner({
  sessionId,
  sessionName,
  initialMessages = [],
}: MealPlannerProps) {
  const connectionState = useConnectionState();
  const participants = useParticipants();
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  const [debugMessages, setDebugMessages] = useState<ChatMessage[]>([]);

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

  const handleAddDebugMessage = (role: 'user' | 'assistant', content: MessageContent) => {
    const newMessage: ChatMessage = {
      id: `debug-${Date.now()}-${Math.random()}`,
      role,
      content,
      timestamp: new Date(),
    };
    setDebugMessages((prev) => [...prev, newMessage]);
  };

  const handleClearMessages = () => {
    setDebugMessages([]);
  };

  return (
    <div className={classNames('flex flex-1 flex-col w-full max-w-7xl mx-auto')}>
      {/* Header */}
      <div className="p-4 border-b border-accent/20 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text">{sessionName}</h1>
          <p className="text-sm text-text/70 mt-1">
            {initialMessages.length > 0
              ? `${initialMessages.length} message${initialMessages.length !== 1 ? 's' : ''} in this session`
              : 'Plan your meals with AI assistance'}
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

        {/* Debug toggle */}
        <button
          onClick={() => setShowDebugPanel(!showDebugPanel)}
          className={classNames(
            'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
            {
              'bg-primary text-white': showDebugPanel,
              'bg-accent/20 text-text hover:bg-accent/30': !showDebugPanel,
            }
          )}
        >
          {showDebugPanel ? '✓ Debug Mode' : 'Debug Mode'}
        </button>
      </div>

      {/* Main Chat Area with Optional Debug Panel */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          <Chat
            showDebugPanel={showDebugPanel}
            debugMessages={debugMessages}
            sessionId={sessionId}
            initialMessages={initialMessages}
          />
        </div>

        {showDebugPanel && (
          <ChatDebugPanel
            onAddMessage={handleAddDebugMessage}
            onClear={handleClearMessages}
          />
        )}
      </div>
    </div>
  );
}
