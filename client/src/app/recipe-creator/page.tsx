'use client';

import { useRouter } from 'next/navigation';
import NotebookIcon from '@/components/icons/NotebookIcon';

export default function RecipeCreatorPage() {
  const router = useRouter();

  return (
    <div className="flex h-dvh items-center justify-center p-8">
      <div className="max-w-2xl">
        <div className="flex items-start gap-6">
          <NotebookIcon className="h-20 w-20 flex-shrink-0 text-primary" />
          <div>
            <h1 className="mb-3 text-4xl font-bold text-text">
              Recipe Creator
            </h1>
            <p className="mb-6 text-lg text-text/70">
              Create and save custom recipes with AI assistance
            </p>
            <button
              onClick={() => router.push('/recipe-creator/new')}
              className="rounded-lg bg-primary px-8 py-3 text-lg font-medium text-white transition-all hover:bg-primary/90"
            >
              Create a Recipe
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
