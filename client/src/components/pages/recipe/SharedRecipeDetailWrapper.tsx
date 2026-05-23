'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import RecipeDetail from '@/components/shared/RecipeDetail';
import { useAuth } from '@/hooks/useAuth';
import { recipes as recipesApi } from '@/lib/api';
import type { Recipe } from '@/types/recipe';

interface SharedRecipeDetailWrapperProps {
  recipe: Recipe;
  shareToken: string;
}

export default function SharedRecipeDetailWrapper({
  recipe,
  shareToken,
}: SharedRecipeDetailWrapperProps) {
  const { user } = useAuth();
  const router = useRouter();
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const handleAddToMyRecipes = async () => {
    try {
      setIsAdding(true);
      setAddError(null);
      const response = await recipesApi.addSharedToMyRecipes(shareToken);
      if (response.error) throw new Error(response.error);
      if (response.data?.recipe_id) {
        router.push(`/recipe/${response.data.recipe_id}`);
      }
    } catch {
      setAddError('Failed to add recipe. Please try again.');
      setIsAdding(false);
    }
  };

  return (
    <>
      {addError && (
        <div className="px-4 sm:px-6 lg:px-8 pt-4">
          <div className="p-3 bg-red-100 text-red-800 text-sm rounded">
            {addError}
          </div>
        </div>
      )}
      <RecipeDetail
        recipe={recipe}
        mode="shared"
        onAddToMyRecipes={handleAddToMyRecipes}
        isAddingToMyRecipes={isAdding}
      />
    </>
  );
}
