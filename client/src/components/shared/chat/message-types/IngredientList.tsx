import classNames from 'classnames';
import type { ChatIngredient } from '@/types/chat-message-types';

export interface IngredientListProps {
  title?: string;
  items: ChatIngredient[];
  isUser?: boolean;
}

/**
 * Component for displaying a list of ingredients with quantities and units.
 * Used in meal planner for shopping lists and recipe ingredients.
 */
export default function IngredientList({
  title,
  items,
  isUser = false,
}: IngredientListProps) {
  return (
    <div className="space-y-3">
      {title && (
        <h3
          className={classNames('font-semibold text-base', {
            'text-white': isUser,
            'text-text': !isUser,
          })}
        >
          {title}
        </h3>
      )}
      <div className="space-y-2">
        {items.map((ingredient) => (
          <div
            key={`${ingredient.name}-${ingredient.amount || ''}-${ingredient.unit || ''}`}
            className={classNames(
              'flex items-start gap-3 p-2 rounded-lg transition-colors',
              {
                'bg-white/10 hover:bg-white/15': isUser,
                'bg-accent/10 hover:bg-accent/15': !isUser,
              },
            )}
          >
            {/* Bullet point or checkbox */}
            <div
              className={classNames('mt-1 flex-shrink-0', {
                'text-white/70': isUser,
                'text-primary': !isUser,
              })}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <circle cx="10" cy="10" r="3" />
              </svg>
            </div>

            {/* Ingredient details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 flex-wrap">
                {ingredient.amount && (
                  <span
                    className={classNames('font-medium', {
                      'text-white': isUser,
                      'text-text': !isUser,
                    })}
                  >
                    {ingredient.amount}
                  </span>
                )}
                {ingredient.unit && (
                  <span
                    className={classNames('text-sm', {
                      'text-white/80': isUser,
                      'text-text/80': !isUser,
                    })}
                  >
                    {ingredient.unit}
                  </span>
                )}
                <span
                  className={classNames('font-medium', {
                    'text-white': isUser,
                    'text-text': !isUser,
                  })}
                >
                  {ingredient.name}
                </span>
              </div>
              {ingredient.notes && (
                <p
                  className={classNames('text-xs mt-1', {
                    'text-white/60': isUser,
                    'text-text/60': !isUser,
                  })}
                >
                  {ingredient.notes}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
      {items.length === 0 && (
        <p
          className={classNames('text-sm italic', {
            'text-white/60': isUser,
            'text-text/60': !isUser,
          })}
        >
          No ingredients listed
        </p>
      )}
    </div>
  );
}
