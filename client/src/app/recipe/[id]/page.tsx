import { Suspense } from 'react';
import RecipeContent from '@/components/pages/recipe/RecipeContent';
import RecipeContentSkeleton from '@/components/pages/recipe/RecipeContentSkeleton';

interface RecipePageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function RecipePage({ params }: RecipePageProps) {
  const { id } = await params;

  return (
    <div className="overflow-auto bg-background">
      <div className="mx-auto max-w-4xl">
        <Suspense fallback={<RecipeContentSkeleton />}>
          <RecipeContent id={id} />
        </Suspense>
      </div>
    </div>
  );
}
