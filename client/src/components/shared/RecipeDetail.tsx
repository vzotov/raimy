'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import ClockIcon from '@/components/icons/ClockIcon';
import EditIcon from '@/components/icons/EditIcon';
import HourglassIcon from '@/components/icons/HourglassIcon';
import InstacartCarrotIcon from '@/components/icons/InstacartCarrotIcon';
import TrashIcon from '@/components/icons/TrashIcon';
import UsersIcon from '@/components/icons/UsersIcon';
import IngredientList from '@/components/shared/IngredientList';
import NutritionSection from '@/components/shared/NutritionSection';
import StepList from '@/components/shared/StepList';
import { useKitchenSessions } from '@/hooks/useSessions';
import { recipes } from '@/lib/api';
import { useConfig } from '@/providers/ConfigProvider';
import type { Recipe } from '@/types/recipe';

interface RecipeDetailProps {
  recipe: Recipe;
}

export default function RecipeDetail({ recipe }: RecipeDetailProps) {
  const router = useRouter();
  const { createSession } = useKitchenSessions();
  const config = useConfig();
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isOrderingIngredients, setIsOrderingIngredients] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendToKitchen = async () => {
    try {
      setIsCreating(true);
      setError(null);
      const session = await createSession(recipe.id);
      if (session) {
        router.push(`/kitchen/${session.id}`);
      }
    } catch (err) {
      console.error('Error creating kitchen session:', err);
      setError('Failed to start cooking session. Please try again.');
      setIsCreating(false);
    }
  };

  const handleEdit = () => {
    if (recipe.chat_session_id) {
      router.push(`/recipe-creator/${recipe.chat_session_id}`);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this recipe?')) {
      return;
    }

    try {
      setIsDeleting(true);
      setError(null);
      const response = await recipes.delete(recipe.id);
      if (response.error) {
        throw new Error(response.error);
      }
      // Navigate to my recipes page after deletion
      router.push('/myrecipes');
    } catch (err) {
      console.error('Failed to delete recipe:', err);
      setError('Failed to delete recipe. Please try again.');
      setIsDeleting(false);
    }
  };

  const handleOrderIngredients = async () => {
    try {
      setIsOrderingIngredients(true);
      setError(null);
      const response = await recipes.getInstacartLink(recipe.id);
      if (response.data?.products_link_url) {
        window.open(
          response.data.products_link_url,
          '_blank',
          'noopener,noreferrer',
        );
      } else if (response.error) {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error('Error generating Instacart link:', err);
      setError('Failed to generate shopping link. Please try again.');
    } finally {
      setIsOrderingIngredients(false);
    }
  };

  return (
    <>
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-text/10 py-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-text px-4 sm:px-6 lg:px-8">
          {recipe.name}
        </h1>
      </div>

      {/* Recipe Info */}
      <div className="flex items-center gap-6 text-text/70 mb-6 px-4 sm:px-6 lg:px-8">
        <span className="flex items-center gap-2">
          <ClockIcon className="w-5 h-5" />
          {recipe.total_time_minutes} min
        </span>
        <span className="flex items-center gap-2">
          <UsersIcon className="w-5 h-5" />
          {recipe.servings} servings
        </span>
        <span
          className={`px-3 py-1 text-sm font-medium rounded-full ${
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

      {/* Description */}
      {recipe.description && (
        <p className="text-text/80 text-base mb-6 px-4 sm:px-6 lg:px-8">
          {recipe.description}
        </p>
      )}

      {/* Tags */}
      {recipe.tags && recipe.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6 px-4 sm:px-6 lg:px-8">
          {recipe.tags.map((tag) => (
            <span
              key={tag}
              className="px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Nutrition */}
      {recipe.nutrition && (
        <div className="mb-8 px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-text mb-4">Nutrition</h2>
          <NutritionSection
            nutrition={recipe.nutrition}
            servings={recipe.servings}
          />
        </div>
      )}

      {/* Ingredients */}
      {recipe.ingredients && recipe.ingredients.length > 0 && (
        <div className="mb-8 px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-text mb-4">Ingredients</h2>
          <IngredientList ingredients={recipe.ingredients} />
        </div>
      )}

      {/* Steps */}
      {recipe.steps && recipe.steps.length > 0 && (
        <div className="mb-8 px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-semibold text-text mb-4">Instructions</h2>
          <StepList steps={recipe.steps} />
        </div>
      )}

      {/* Sticky Action Buttons */}
      <div className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-text/10 py-4 mt-8">
        <div className="px-4 sm:px-6 lg:px-8">
          {error && (
            <div className="p-3 bg-red-100 text-red-800 text-sm rounded mb-3">
              {error}
            </div>
          )}
          <div className="flex flex-col sm:flex-row gap-3 sm:justify-center">
            <button
              onClick={handleSendToKitchen}
              disabled={isCreating}
              className="sm:w-auto px-6 py-3 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
            >
              {isCreating ? (
                <>
                  <HourglassIcon className="animate-spin w-5 h-5" />
                  Starting...
                </>
              ) : (
                <>
                  <ChefHatIcon className="w-5 h-5" />
                  Send to Kitchen
                </>
              )}
            </button>

            {config.instacart_enabled && (
              <button
                onClick={handleOrderIngredients}
                disabled={isOrderingIngredients || !recipe.ingredients?.length}
                className="sm:w-auto px-6 py-3 bg-surface hover:bg-surface/70 text-text font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-text/10 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isOrderingIngredients ? (
                  <>
                    <HourglassIcon className="animate-spin w-5 h-5" />
                    Opening...
                  </>
                ) : (
                  <>
                    <InstacartCarrotIcon className="w-6 h-6" />
                    <span className="flex flex-col items-start leading-tight">
                      <span>Order Ingredients</span>
                      <span className="text-xs text-text/60">
                        via Instacart
                      </span>
                    </span>
                  </>
                )}
              </button>
            )}

            {recipe.chat_session_id && (
              <button
                onClick={handleEdit}
                className="sm:w-auto px-6 py-3 bg-surface hover:bg-surface/70 text-text font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-text/10 cursor-pointer"
              >
                <EditIcon className="w-5 h-5" />
                Edit in Creator
              </button>
            )}

            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="sm:w-auto px-6 py-3 bg-surface hover:bg-surface/70 text-text font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-text/10 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isDeleting ? (
                <>
                  <HourglassIcon className="animate-spin w-5 h-5" />
                  Deleting...
                </>
              ) : (
                <>
                  <TrashIcon className="w-5 h-5" />
                  Delete Recipe
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Metadata */}
      {recipe.created_at && (
        <div className="border-t border-text/10 pt-4 mb-4">
          <div className="text-xs text-text/50 px-4 sm:px-6 lg:px-8">
            Created: {new Date(recipe.created_at).toLocaleDateString()}
          </div>
        </div>
      )}
    </>
  );
}
