'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Chat from '@/components/shared/chat/Chat';
import { ChatHeader } from '@/components/shared/ChatHeader';
import RecipeDocument from '@/components/shared/RecipeDocument';
import SlidingPanel from '@/components/shared/SlidingPanel';
import SlidingPanelTrigger from '@/components/shared/SlidingPanelTrigger';
import { useChatSessionTitle } from '@/hooks/useChatSessionTitle';
import { useUnifiedChatState } from '@/hooks/useUnifiedChatState';
import { useWebSocket } from '@/hooks/useWebSocket';
import { chatSessions } from '@/lib/api';
import { useConfig } from '@/providers/ConfigProvider';
import type { SessionMessage } from '@/types/chat-session';
import type { KitchenStepContent } from '@/types/chat-message-types';
import type { Recipe } from '@/types/recipe';
import CookingView from './CookingView';

interface UnifiedChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
  initialFinished?: boolean;
  initialRecipe?: Recipe | null;
  initialIsChanged?: boolean;
}

export default function UnifiedChat({
  sessionId,
  sessionName,
  initialMessages = [],
  initialFinished = false,
  initialRecipe = null,
  initialIsChanged = false,
}: UnifiedChatProps) {
  const router = useRouter();
  const config = useConfig();

  const state = useUnifiedChatState({
    sessionId,
    initialMessages,
    initialFinished,
    initialRecipe,
    initialIsChanged,
  });

  const [mode, setMode] = useState<'chat' | 'cook'>('chat');
  const [isRecipePanelOpen, setIsRecipePanelOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Switch to COOK mode when first kitchen-step arrives
  useEffect(() => {
    if (state.cookingStarted && mode === 'chat') {
      setMode('cook');
    }
  }, [state.cookingStarted, mode]);

  // Auto-open recipe panel when recipe first appears
  const hasRecipe = !!state.recipe;
  useEffect(() => {
    if (hasRecipe && mode === 'chat') {
      setIsRecipePanelOpen(true);
    }
  }, [hasRecipe, mode]);

  useChatSessionTitle(state.sessionName || sessionName);

  const { sendMessage, isConnected, error } = useWebSocket({
    sessionId,
    onMessage: state.handleMessage,
    autoReconnect: !state.cookingComplete,
  });

  const handleSendMessage = useCallback(
    (content: string) => {
      state.addMessage(content);
      sendMessage(content);
    },
    [state.addMessage, sendMessage],
  );

  const handleSaveRecipe = useCallback(async () => {
    if (!state.recipe) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      const response = await chatSessions.saveRecipe(sessionId);
      if (response.error) {
        setSaveError(response.error);
        return;
      }
      if (response.data?.recipe) {
        state.setRecipe(response.data.recipe);
      }
      state.resetChangedFlag();
    } catch {
      setSaveError('Failed to save recipe. Please try again.');
    } finally {
      setIsSaving(false);
    }
  }, [state.recipe, sessionId, state.setRecipe, state.resetChangedFlag]);

  const handleStepImageGenerated = useCallback(
    (stepIndex: number, imageUrl: string) => {
      state.applyRecipeUpdate({
        type: 'recipe_update',
        action: 'set_step_image',
        step_index: stepIndex,
        image_url: imageUrl,
      });
    },
    [state.applyRecipeUpdate],
  );

  // Collect all kitchen-step messages received so far
  const allSteps = useMemo(
    () =>
      state.messages
        .filter((m) => m.content.type === 'kitchen-step')
        .map((m) => m.content as KitchenStepContent),
    [state.messages],
  );

  // Total steps from recipe if available, else from steps received so far
  const totalSteps = state.recipe?.steps?.length ?? allSteps.length;

  if (state.cookingComplete) {
    const lastAssistant = [...state.messages].reverse().find((m) => m.role === 'assistant');
    const finalMessage =
      lastAssistant?.content && 'content' in lastAssistant.content
        ? (lastAssistant.content as { content: string }).content
        : lastAssistant?.content && 'message' in lastAssistant.content
          ? (lastAssistant.content as { message: string }).message
          : null;

    return (
      <div className="flex h-full w-full flex-col items-center justify-center p-8">
        <div className="max-w-lg text-center">
          <div className="mb-4 text-6xl">🎉</div>
          <h1 className="mb-4 text-3xl font-bold text-text">
            {state.sessionName || sessionName}
          </h1>
          {finalMessage && <p className="text-lg text-text/80">{finalMessage}</p>}
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => router.push('/chat/new')}
              className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-white transition-colors hover:bg-primary/90"
            >
              Cook Something New
            </button>
            <button
              onClick={() => router.push('/myrecipes')}
              className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-text/10 bg-surface px-6 py-3 font-medium text-text transition-colors hover:bg-surface/70"
            >
              Browse My Recipes
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'cook') {
    return (
      <CookingView
        allSteps={allSteps}
        totalSteps={totalSteps}
        onNext={() => handleSendMessage('next step')}
        onPrev={() => handleSendMessage('previous step')}
        onBack={() => setMode('chat')}
        agentStatus={state.agentStatus}
        messages={state.messages}
        onSendMessage={handleSendMessage}
        isConnected={isConnected}
      />
    );
  }

  return (
    <div className="flex h-full w-full overflow-hidden">
      <div className="flex min-w-0 flex-1 flex-col">
        <ChatHeader
          title={state.sessionName || sessionName}
          isConnected={isConnected}
          error={error}
        />
        <div className="min-h-0 flex-1 overflow-hidden">
          <Chat
            messages={state.messages}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            agentStatus={state.agentStatus}
            placeholder="Ask me anything, or tell me what you'd like to cook..."
          />
        </div>
      </div>

      {state.recipe && !isRecipePanelOpen && (
        <SlidingPanelTrigger
          onClick={() => setIsRecipePanelOpen(true)}
          icon={
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          }
          label="Recipe"
          indicator={state.isRecipeChanged}
        />
      )}

      <SlidingPanel isOpen={isRecipePanelOpen} onClose={() => setIsRecipePanelOpen(false)}>
        <RecipeDocument
          recipe={state.recipe}
          onToggle={() => setIsRecipePanelOpen(false)}
          onSave={handleSaveRecipe}
          isSaving={isSaving}
          saveError={saveError}
          isRecipeChanged={state.isRecipeChanged}
          onClearError={() => setSaveError(null)}
          sessionId={sessionId}
          imageGenEnabled={config.image_gen_enabled}
          onStepImageGenerated={handleStepImageGenerated}
        />
      </SlidingPanel>
    </div>
  );
}
