import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import { Suspense } from 'react';
import RecipeContent from '@/components/pages/recipe/RecipeContent';
import RecipeContentSkeleton from '@/components/pages/recipe/RecipeContentSkeleton';

interface RecipePageProps {
  params: Promise<{
    id: string;
  }>;
}

export async function generateMetadata({
  params,
}: RecipePageProps): Promise<Metadata> {
  const { id } = await params;
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const res = await fetch(`${apiUrl}/api/recipes/${id}`, {
      headers: { Cookie: cookieStore.toString() },
    });

    if (!res.ok) {
      return { title: 'Recipe' };
    }

    const data = await res.json();
    return { title: data.recipe?.name || 'Recipe' };
  } catch {
    return { title: 'Recipe' };
  }
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
