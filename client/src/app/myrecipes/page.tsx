import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import RecipeCard, { type Recipe } from '@/components/shared/RecipeCard';

export default async function MyRecipesPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  let recipes: Recipe[] = [];

  try {
    const response = await fetch(`${apiUrl}/api/recipes`, {
      headers: {
        Cookie: cookieStore.toString(),
      },
      cache: 'no-store',
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

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text">My Recipes</h1>
          <p className="mt-2 text-text/70">
            {recipes.length === 0
              ? "You haven't created any recipes yet. Start cooking with Raimy to see your recipes here!"
              : `You have ${recipes.length} recipe${recipes.length === 1 ? '' : 's'}`}
          </p>
        </div>

        {recipes.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">👨‍🍳</div>
            <h3 className="text-xl font-semibold text-text mb-2">
              No recipes yet
            </h3>
            <p className="text-text/70 mb-6">
              Start cooking with Raimy to create your first recipe!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
