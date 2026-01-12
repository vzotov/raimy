import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import RecipeDetail from '@/components/shared/RecipeDetail';

interface RecipePageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function RecipePage({ params }: RecipePageProps) {
  const { id } = await params;
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const recipeRes = await fetch(`${apiUrl}/api/recipes/${id}`, {
      headers: { Cookie: cookieStore.toString() },
      cache: 'no-store',
    });

    if (!recipeRes.ok) {
      if (recipeRes.status === 404) notFound();
      throw new Error('Failed to fetch recipe');
    }

    const recipeData = await recipeRes.json();

    return (
      <div className="overflow-auto bg-background">
        <div className="mx-auto max-w-4xl">
          <RecipeDetail recipe={recipeData.recipe} />
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error fetching recipe:', error);
    notFound();
  }
}
