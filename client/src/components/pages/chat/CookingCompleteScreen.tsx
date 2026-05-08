'use client';

import HourglassIcon from '@/components/icons/HourglassIcon';
import SaveIcon from '@/components/icons/SaveIcon';
import type { Recipe } from '@/types/recipe';

interface CookingCompleteScreenProps {
  sessionName: string;
  finalMessage: string | null;
  recipe: Recipe | null;
  isSaving: boolean;
  saveError: string | null;
  isRecipeChanged: boolean;
  onSave: () => void;
  onClearError: () => void;
  onReturnToChat: () => void;
  onNewChat: () => void;
  onBrowseRecipes: () => void;
}

export default function CookingCompleteScreen({
  sessionName,
  finalMessage,
  recipe,
  isSaving,
  saveError,
  isRecipeChanged,
  onSave,
  onClearError,
  onReturnToChat,
  onNewChat,
  onBrowseRecipes,
}: CookingCompleteScreenProps) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center p-8">
      <div className="max-w-lg w-full text-center">
        <div className="mb-4 text-6xl">🎉</div>
        <h1 className="mb-4 text-3xl font-bold text-text">{sessionName}</h1>
        {finalMessage && <p className="text-lg text-text/80">{finalMessage}</p>}

        <div className="mt-8 flex flex-col gap-3">
          {recipe && (
            <div>
              {saveError && (
                <div className="mb-3 p-2 bg-red-100 text-red-800 text-sm rounded flex items-center justify-between">
                  <span>{saveError}</span>
                  <button onClick={onClearError} className="ml-2 hover:opacity-70 text-lg leading-none">
                    ×
                  </button>
                </div>
              )}
              <button
                onClick={onSave}
                disabled={!isRecipeChanged || isSaving}
                className="w-full px-4 py-3 bg-primary hover:bg-primary/90
                           disabled:bg-primary/50 disabled:cursor-not-allowed
                           text-white font-medium rounded-lg transition-colors
                           flex items-center justify-center gap-2"
              >
                {isSaving ? (
                  <>
                    <HourglassIcon className="animate-spin w-5 h-5" />
                    Saving...
                  </>
                ) : isRecipeChanged ? (
                  <>
                    <SaveIcon className="w-5 h-5" />
                    Save Recipe
                  </>
                ) : (
                  <>
                    <SaveIcon className="w-5 h-5" />
                    Saved
                  </>
                )}
              </button>
            </div>
          )}

          <button
            onClick={onReturnToChat}
            className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-text/10 bg-surface px-6 py-3 font-medium text-text transition-colors hover:bg-surface/70"
          >
            Return to Chat
          </button>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              onClick={onNewChat}
              className="flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg border border-text/10 bg-surface px-6 py-3 font-medium text-text transition-colors hover:bg-surface/70"
            >
              Cook Something New
            </button>
            <button
              onClick={onBrowseRecipes}
              className="flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg border border-text/10 bg-surface px-6 py-3 font-medium text-text transition-colors hover:bg-surface/70"
            >
              Browse My Recipes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
