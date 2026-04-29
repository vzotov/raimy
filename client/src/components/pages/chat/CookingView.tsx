'use client';

import { useState } from 'react';
import Chat from '@/components/shared/chat/Chat';
import SlidingPanel from '@/components/shared/SlidingPanel';
import type { ChatMessage } from '@/hooks/useChatMessages';
import type { KitchenStepContent } from '@/types/chat-message-types';
import CookingStep from './CookingStep';

interface CookingViewProps {
  allSteps: KitchenStepContent[];
  totalSteps: number;
  onNext: () => void;
  onPrev: () => void;
  onBack: () => void;
  agentStatus: string | null;
  // Chat overlay
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  isConnected: boolean;
}

export default function CookingView({
  allSteps,
  totalSteps,
  onNext,
  onPrev,
  onBack,
  agentStatus,
  messages,
  onSendMessage,
  isConnected,
}: CookingViewProps) {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const currentStepIndex = allSteps.length > 0 ? allSteps.length - 1 : 0;
  const currentStep = allSteps[currentStepIndex] ?? null;
  const isLoading = agentStatus === 'thinking';

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex shrink-0 items-center justify-between border-b border-accent/20 px-4 py-3">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-text/60 transition-colors hover:text-text"
        >
          <span>←</span>
          <span>Back to Chat</span>
        </button>

        <button
          onClick={() => setIsChatOpen(true)}
          className="rounded-lg border border-accent/20 bg-surface px-3 py-1.5 text-sm font-medium text-text transition-colors hover:bg-accent/10"
        >
          Ask a question
        </button>
      </div>

      {/* Step display */}
      <div className="min-h-0 flex-1">
        {currentStep ? (
          <CookingStep
            step={currentStep}
            stepIndex={currentStepIndex}
            totalSteps={totalSteps}
            onNext={onNext}
            onPrev={onPrev}
            hasPrev={currentStepIndex > 0}
            isLoading={isLoading}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-text/40">
            <span className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}
      </div>

      {/* Chat overlay */}
      <SlidingPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)}>
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex shrink-0 items-center justify-between border-b border-accent/20 p-4">
            <h2 className="text-base font-semibold text-text">Ask Raimy</h2>
            <button
              onClick={() => setIsChatOpen(false)}
              className="p-1 text-text/40 transition-colors hover:text-text"
            >
              ✕
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-hidden">
            <Chat
              messages={messages}
              onSendMessage={onSendMessage}
              isConnected={isConnected}
              agentStatus={agentStatus}
              placeholder="Ask about this step..."
            />
          </div>
        </div>
      </SlidingPanel>
    </div>
  );
}
