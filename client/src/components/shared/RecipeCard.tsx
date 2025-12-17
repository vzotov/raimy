'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useKitchenSessions } from '@/hooks/useSessions';

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

export interface Recipe {
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

interface RecipeCardProps {
  recipe: Recipe;
}

export default function RecipeCard({ recipe }: RecipeCardProps) {
  const router = useRouter();
  const { createSession } = useKitchenSessions();
  const [isCreating, setIsCreating] = useState(false);
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
  return (
    <div className="bg-surface rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
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

        <button
          onClick={handleSendToKitchen}
          disabled={isCreating}
          className="w-full mb-3 px-4 py-2 bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isCreating ? (
            <>
              <span className="animate-spin">⏳</span>
              Starting...
            </>
          ) : (
            <>
              <span>👨‍🍳</span>
              Send to Kitchen
            </>
          )}
        </button>

        {error && (
          <div className="mb-3 p-2 bg-red-100 text-red-800 text-sm rounded">
            {error}
          </div>
        )}

        <div className="text-xs text-text/50">
          Created: {new Date(recipe.created_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}