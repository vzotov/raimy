import type { Metadata } from 'next';
import { Suspense } from 'react';
import RecipeList from '@/components/pages/myrecipes/RecipeList';
import { RecipeListSkeleton } from '@/components/pages/myrecipes/RecipeListSkeleton';
export const metadata: Metadata = {
  title: 'My Recipes',
};

export default function MyRecipesPage() {
  return (
    <div className="min-h-dvh bg-background py-8 pb-24 sm:pb-8 overflow-auto">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text">My Recipes</h1>
        </div>

        <Suspense
          fallback={
            <>
              <p className="text-text/70 mb-8">Loading your recipes...</p>
              <RecipeListSkeleton count={6} />
            </>
          }
        >
          <RecipeList />
        </Suspense>
      </div>
    </div>
  );
}
