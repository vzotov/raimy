'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { get } from '@/lib/api';
import CreateFakeRecipeButton from './CreateFakeRecipeButton';

interface RecipeIngredient {
  name: string;
  amount?: string;
  unit?: string;
  notes?: string;
}

interface RecipeStep {
  instruction: string;
  duration?: number;
}

interface Recipe {
  id: string;
  name: string;
  description: string;
  ingredients: RecipeIngredient[];
  steps: RecipeStep[];
  total_time_minutes: number;
  difficulty: string;
  servings: number;
  tags: string[];
  user_id: string;
  created_at: string;
  updated_at: string;
}

export default function MyRecipesContent() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecipes = async () => {
    try {
      setLoading(true);
      const result = await get<{ recipes: Recipe[] }>('/api/recipes');

      if (result.error) {
        throw new Error(result.error);
      }

      setRecipes(result.data?.recipes || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recipes');
      console.error('Error fetching recipes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">Loading recipes...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-text">My Recipes</h1>
              <p className="mt-2 text-text/70">
                {recipes.length === 0
                  ? "You haven't created any recipes yet. Start cooking with Raimy to see your recipes here!"
                  : `You have ${recipes.length} recipe${recipes.length === 1 ? '' : 's'}`}
              </p>
            </div>
            <CreateFakeRecipeButton onRecipeCreated={fetchRecipes} />
          </div>
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
            <Link
              href="/kitchen"
              className="inline-flex items-center px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors"
            >
              Go to Kitchen
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recipes.map((recipe) => (
              <div
                key={recipe.id}
                className="bg-surface rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-xl font-semibold text-text line-clamp-2">
                      {recipe.name}
                    </h3>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        recipe.difficulty === 'easy'
                          ? 'bg-green-100 text-green-800'
                          : recipe.difficulty === 'medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {recipe.difficulty}
                    </span>
                  </div>

                  <p className="text-text/70 text-sm mb-4 line-clamp-3">
                    {recipe.description}
                  </p>

                  <div className="flex items-center justify-between text-sm text-text/60 mb-4">
                    <span>⏱️ {recipe.total_time_minutes} min</span>
                    <span>👥 {recipe.servings} servings</span>
                  </div>

                  <div className="mb-4">
                    <h4 className="font-medium text-text mb-2">Ingredients:</h4>
                    <ul className="text-sm text-text/70 space-y-1">
                      {recipe.ingredients
                        .slice(0, 3)
                        .map((ingredient, index) => (
                          <li key={index} className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-primary rounded-full mr-2"></span>
                            {ingredient.amount && `${ingredient.amount} `}
                            {ingredient.unit && `${ingredient.unit} `}
                            {ingredient.name}
                          </li>
                        ))}
                      {recipe.ingredients.length > 3 && (
                        <li className="text-text/60 italic">
                          +{recipe.ingredients.length - 3} more ingredients
                        </li>
                      )}
                    </ul>
                  </div>

                  <div className="mb-4">
                    <h4 className="font-medium text-text mb-2">Steps:</h4>
                    <div className="text-sm text-text/70 space-y-1">
                      {recipe.steps.slice(0, 2).map((step, index) => (
                        <div key={index} className="flex items-start">
                          <span className="bg-primary/20 text-primary text-xs font-medium px-2 py-1 rounded-full mr-2 mt-0.5">
                            {index + 1}
                          </span>
                          <span className="line-clamp-2">
                            {step.instruction}
                          </span>
                        </div>
                      ))}
                      {recipe.steps.length > 2 && (
                        <div className="text-text/60 italic">
                          +{recipe.steps.length - 2} more steps
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1 mb-4">
                    {recipe.tags.slice(0, 3).map((tag) => (
                      <span
                        key={`tag-${tag}`}
                        className="px-2 py-1 bg-surface/50 text-text/80 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {recipe.tags.length > 3 && (
                      <span className="text-text/60 text-xs">
                        +{recipe.tags.length - 3} more
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-text/50">
                    Created: {new Date(recipe.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
