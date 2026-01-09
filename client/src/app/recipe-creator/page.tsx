'use client';

import classNames from 'classnames';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useRecipeCreatorSessions } from '@/hooks/useSessions';
import NotebookIcon from '@/components/icons/NotebookIcon';

export default function RecipeCreatorPage() {
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { createSession } = useRecipeCreatorSessions();

  const handleCreateRecipe = async () => {
    try {
      setIsCreating(true);
      setError(null);

      const session = await createSession();

      if (session?.id) {
        router.push(`/recipe-creator/${session.id}`);
      }
    } catch (err) {
      console.error('Failed to create recipe creator session:', err);
      setError('Failed to create session. Please try again.');
      setIsCreating(false);
    }
  };

  return (
    <div className="flex h-screen h-dvh items-center justify-center p-8">
      <div className="max-w-2xl">
        <div className="flex items-start gap-6">
          <NotebookIcon className="w-20 h-20 text-primary flex-shrink-0" />
          <div>
            <h1 className="text-4xl font-bold text-text mb-3">
              Recipe Creator
            </h1>
            <p className="text-lg text-text/70 mb-6">
              Create and save custom recipes with AI assistance
            </p>
            <button
              onClick={handleCreateRecipe}
              disabled={isCreating}
              className={classNames(
                'px-8 py-3 rounded-lg font-medium transition-all text-lg',
                {
                  'bg-primary text-white hover:bg-primary/90': !isCreating,
                  'bg-accent/20 text-text/30 cursor-not-allowed': isCreating,
                },
              )}
            >
              {isCreating ? 'Creating...' : 'Create a Recipe'}
            </button>
            {error && (
              <div className="mt-4 bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-500 text-sm">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
