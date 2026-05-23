import type { Metadata } from 'next';
import { Suspense } from 'react';
import SharedRecipeContent from '@/components/pages/recipe/SharedRecipeContent';
import RecipeContentSkeleton from '@/components/pages/recipe/RecipeContentSkeleton';

interface SharedRecipePageProps {
  params: Promise<{
    token: string;
  }>;
}

export async function generateMetadata({
  params,
}: SharedRecipePageProps): Promise<Metadata> {
  const { token } = await params;
  const apiUrl = process.env.API_URL || 'http://localhost:8000';

  try {
    const res = await fetch(`${apiUrl}/api/recipes/shared/${token}`, {
      cache: 'no-store',
    });
    if (!res.ok) return { title: 'Recipe' };
    const data = await res.json();
    return { title: data.recipe?.name || 'Recipe' };
  } catch {
    return { title: 'Recipe' };
  }
}

export default async function SharedRecipePage({
  params,
}: SharedRecipePageProps) {
  const { token } = await params;

  return (
    <div className="overflow-auto bg-background">
      <div className="mx-auto max-w-4xl">
        <Suspense fallback={<RecipeContentSkeleton />}>
          <SharedRecipeContent token={token} />
        </Suspense>
      </div>
    </div>
  );
}
