'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import HourglassIcon from '@/components/icons/HourglassIcon';
import TrashIcon from '@/components/icons/TrashIcon';
import { useKitchenSessions } from '@/hooks/useSessions';
import { recipes } from '@/lib/api';
import type { Recipe } from '@/types/recipe';

interface RecipeCardProps {
  recipe: Recipe;
}

export default function RecipeCard({ recipe }: RecipeCardProps) {
  const router = useRouter();
  const { createSession } = useKitchenSessions();
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendToKitchen = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

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

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

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
      // Trigger page refresh to update the list
      router.refresh();
    } catch (err) {
      console.error('Failed to delete recipe:', err);
      setError('Failed to delete recipe. Please try again.');
      setIsDeleting(false);
    }
  };

  return (
    <Link href={`/recipe/${recipe.id}`} className="h-full">
      <div className="bg-surface rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer h-full flex flex-col">
        <div className="p-6 flex flex-col flex-1">
          {/* Recipe Name */}
          <h3 className="text-xl font-semibold text-text mb-4 line-clamp-2">
            {recipe.name}
          </h3>

          {/* Description */}
          {recipe.description && (
            <p className="text-text/70 text-sm mb-4 line-clamp-3">
              {recipe.description}
            </p>
          )}

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-4">
            {recipe.tags?.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1.5 bg-primary/10 text-primary text-xs font-medium rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Nutrition - calories only for compact view */}
          {recipe.nutrition?.calories && (
            <div className="text-sm text-text/60 mb-4">
              {recipe.nutrition.calories} cal
              {recipe.servings && recipe.servings > 1 && (
                <span className="text-text/40">
                  {' '}
                  ({Math.round(recipe.nutrition.calories / recipe.servings)} per
                  serving)
                </span>
              )}
            </div>
          )}

          {/* Spacer to push buttons to bottom */}
          <div className="flex-1"></div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleSendToKitchen}
              disabled={isCreating}
              className="flex-1 px-4 py-2 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
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

            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="px-4 py-2 bg-surface hover:bg-surface/70 text-text/50 hover:text-red-500 border border-text/10 font-medium rounded-lg transition-colors flex items-center justify-center cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              title="Delete recipe"
            >
              <TrashIcon className="w-5 h-5" />
            </button>
          </div>

          {error && (
            <div className="mt-3 p-2 bg-red-100 text-red-800 text-sm rounded">
              {error}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
