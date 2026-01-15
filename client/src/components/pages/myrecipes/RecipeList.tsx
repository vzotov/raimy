import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import RecipeCard from '@/components/shared/RecipeCard';
import type { Recipe } from '@/types/recipe';

export default async function RecipeList() {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  let recipes: Recipe[] = [];

  try {
    const response = await fetch(`${apiUrl}/api/recipes/`, {
      headers: {
        Cookie: cookieStore.toString(),
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        redirect('/');
      }
      throw new Error(`Failed to fetch recipes: ${response.statusText}`);
    }

    const data = await response.json();
    recipes = data.recipes || [];
  } catch (error) {
    console.error('Error fetching recipes:', error);
    throw error;
  }

  if (recipes.length === 0) {
    return (
      <>
        <p className="text-text/70 mb-8">
          You haven&apos;t created any recipes yet. Start cooking with Raimy to
          see your recipes here!
        </p>
        <div className="py-12">
          <div className="flex items-start gap-6 mb-6">
            <ChefHatIcon className="w-20 h-20 text-primary flex-shrink-0" />
            <div>
              <h3 className="text-xl font-semibold text-text mb-2">
                No recipes yet
              </h3>
              <p className="text-text/70">
                Start cooking with Raimy to create your first recipe!
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <p className="text-text/70 mb-8">
        You have {recipes.length} recipe{recipes.length === 1 ? '' : 's'}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:auto-rows-fr">
        {recipes.map((recipe) => (
          <RecipeCard key={recipe.id} recipe={recipe} />
        ))}
      </div>
    </>
  );
}
