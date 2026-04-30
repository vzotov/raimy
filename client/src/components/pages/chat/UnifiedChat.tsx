'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Chat from '@/components/shared/chat/Chat';
import { ChatHeader } from '@/components/shared/ChatHeader';
import CookingCompleteScreen from './CookingCompleteScreen';
import RecipeDocument from '@/components/shared/RecipeDocument';
import SlidingPanel from '@/components/shared/SlidingPanel';
import SlidingPanelTrigger from '@/components/shared/SlidingPanelTrigger';
import { useChatSessionTitle } from '@/hooks/useChatSessionTitle';
import { useUnifiedChatState } from '@/hooks/useUnifiedChatState';
import { useWebSocket } from '@/hooks/useWebSocket';
import { chatSessions } from '@/lib/api';
import { useConfig } from '@/providers/ConfigProvider';
import type { SessionMessage } from '@/types/chat-session';
import type { Recipe } from '@/types/recipe';

interface UnifiedChatProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
  initialFinished?: boolean;
  initialRecipe?: Recipe | null;
  initialIsChanged?: boolean;
  initialInput?: string;
}

export default function UnifiedChat({
  sessionId,
  sessionName,
  initialMessages = [],
  initialFinished = false,
  initialRecipe = null,
  initialIsChanged = false,
  initialInput,
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

  const [isRecipePanelOpen, setIsRecipePanelOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [completeScreenDismissed, setCompleteScreenDismissed] = useState(false);

  // Auto-open recipe panel when recipe first appears
  const hasRecipe = !!state.recipe;
  useEffect(() => {
    if (hasRecipe) {
      setIsRecipePanelOpen(true);
    }
  }, [hasRecipe]);

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

  if (state.cookingComplete && !completeScreenDismissed) {
    const lastAssistant = [...state.messages].reverse().find((m) => m.role === 'assistant');
    const finalMessage =
      lastAssistant?.content && 'content' in lastAssistant.content
        ? (lastAssistant.content as { content: string }).content
        : lastAssistant?.content && 'message' in lastAssistant.content
          ? (lastAssistant.content as { message: string }).message
          : null;

    return (
      <CookingCompleteScreen
        sessionName={state.sessionName || sessionName}
        finalMessage={finalMessage}
        recipe={state.recipe}
        isSaving={isSaving}
        saveError={saveError}
        isRecipeChanged={state.isRecipeChanged}
        onSave={handleSaveRecipe}
        onClearError={() => setSaveError(null)}
        onReturnToChat={() => setCompleteScreenDismissed(true)}
        onNewChat={() => router.push('/chat/new')}
        onBrowseRecipes={() => router.push('/myrecipes')}
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
            initialInput={initialInput}
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
