import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import RecipeDetail from '@/components/shared/RecipeDetail';

interface RecipeContentProps {
  id: string;
}

export default async function RecipeContent({ id }: RecipeContentProps) {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const recipeRes = await fetch(`${apiUrl}/api/recipes/${id}`, {
      headers: { Cookie: cookieStore.toString() },
    });

    if (!recipeRes.ok) {
      if (recipeRes.status === 404) notFound();
      throw new Error('Failed to fetch recipe');
    }

    const recipeData = await recipeRes.json();

    return <RecipeDetail recipe={recipeData.recipe} />;
  } catch (error) {
    console.error('Error fetching recipe:', error);
    notFound();
  }
}
