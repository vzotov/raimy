import classNames from 'classnames';
import Link from 'next/link';
import type { RecipeContent } from '@/types/chat-message-types';
import IngredientList from './IngredientList';

export interface RecipeCardProps {
  recipe: RecipeContent;
  isUser?: boolean;
}

/**
 * Component for displaying a recipe card in chat messages.
 * Shows recipe name, description, ingredients, steps, and metadata.
 * Includes a link to view the full recipe in My Recipes.
 */
export default function RecipeCard({
  recipe,
  isUser = false,
}: RecipeCardProps) {
  const difficultyColors = {
    easy: 'bg-green-500/20 text-green-300',
    medium: 'bg-yellow-500/20 text-yellow-300',
    hard: 'bg-red-500/20 text-red-300',
  };

  const difficultyColor = recipe.difficulty
    ? difficultyColors[recipe.difficulty as keyof typeof difficultyColors] ||
      difficultyColors.medium
    : difficultyColors.medium;

  return (
    <div
      className={classNames('rounded-lg overflow-hidden border', {
        'bg-white/5 border-white/10': isUser,
        'bg-accent/5 border-accent/10': !isUser,
      })}
    >
      {/* Header with recipe name */}
      <div
        className={classNames('p-4 border-b', {
          'bg-white/10 border-white/10': isUser,
          'bg-primary/10 border-primary/10': !isUser,
        })}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <h3
              className={classNames('font-bold text-lg mb-2', {
                'text-white': isUser,
                'text-text': !isUser,
              })}
            >
              {recipe.name}
            </h3>
            {recipe.description && (
              <p
                className={classNames('text-sm', {
                  'text-white/80': isUser,
                  'text-text/80': !isUser,
                })}
              >
                {recipe.description}
              </p>
            )}
          </div>

          {/* Difficulty badge */}
          {recipe.difficulty && (
            <span
              className={classNames(
                'px-2 py-1 rounded-full text-xs font-semibold uppercase tracking-wide',
                difficultyColor,
              )}
            >
              {recipe.difficulty}
            </span>
          )}
        </div>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-4 mt-3 text-sm">
          {recipe.total_time_minutes && (
            <div
              className={classNames('flex items-center gap-1', {
                'text-white/70': isUser,
                'text-text/70': !isUser,
              })}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{recipe.total_time_minutes} min</span>
            </div>
          )}
          {recipe.servings && (
            <div
              className={classNames('flex items-center gap-1', {
                'text-white/70': isUser,
                'text-text/70': !isUser,
              })}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span>{recipe.servings} servings</span>
            </div>
          )}
        </div>

        {/* Tags */}
        {recipe.tags && recipe.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {recipe.tags.map((tag) => (
              <span
                key={`tag-${tag}`}
                className={classNames('px-2 py-0.5 rounded-full text-xs', {
                  'bg-white/10 text-white/80': isUser,
                  'bg-primary/10 text-primary': !isUser,
                })}
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Recipe content */}
      <div className="p-4 space-y-4">
        {/* Ingredients section */}
        {recipe.ingredients && recipe.ingredients.length > 0 && (
          <div>
            <h4
              className={classNames('font-semibold text-sm mb-2', {
                'text-white': isUser,
                'text-text': !isUser,
              })}
            >
              Ingredients
            </h4>
            <IngredientList items={recipe.ingredients} isUser={isUser} />
          </div>
        )}

        {/* Steps section */}
        {recipe.steps && recipe.steps.length > 0 && (
          <div>
            <h4
              className={classNames('font-semibold text-sm mb-2', {
                'text-white': isUser,
                'text-text': !isUser,
              })}
            >
              Instructions
            </h4>
            <div className="space-y-3">
              {recipe.steps.map((step, index) => (
                <div
                  key={index}
                  className={classNames('flex gap-3 p-3 rounded-lg', {
                    'bg-white/5': isUser,
                    'bg-accent/5': !isUser,
                  })}
                >
                  {/* Step number */}
                  <div
                    className={classNames(
                      'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs',
                      {
                        'bg-white/20 text-white': isUser,
                        'bg-primary/20 text-primary': !isUser,
                      },
                    )}
                  >
                    {index}
                  </div>

                  {/* Step content */}
                  <div className="flex-1 min-w-0">
                    <p
                      className={classNames('text-sm', {
                        'text-white/90': isUser,
                        'text-text/90': !isUser,
                      })}
                    >
                      {step.instruction}
                    </p>
                    {step.duration_minutes && (
                      <div
                        className={classNames(
                          'flex items-center gap-1 mt-1 text-xs',
                          {
                            'text-white/60': isUser,
                            'text-text/60': !isUser,
                          },
                        )}
                      >
                        <svg
                          className="w-3 h-3"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        <span>{step.duration_minutes} min</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* View in My Recipes link */}
        <div className="pt-3 border-t border-white/10">
          <Link
            href="/myrecipes"
            className={classNames(
              'inline-flex items-center gap-2 text-sm font-medium transition-colors',
              {
                'text-white hover:text-white/80': isUser,
                'text-primary hover:text-primary/80': !isUser,
              },
            )}
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            View in My Recipes
          </Link>
        </div>
      </div>
    </div>
  );
}
