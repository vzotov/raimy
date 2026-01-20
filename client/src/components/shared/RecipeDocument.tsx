import ClockIcon from '@/components/icons/ClockIcon';
import HourglassIcon from '@/components/icons/HourglassIcon';
import SaveIcon from '@/components/icons/SaveIcon';
import NutritionSection from '@/components/shared/NutritionSection';
import SectionTitle from '@/components/shared/SectionTitle';
import type { Recipe } from '@/types/recipe';

interface RecipeDocumentProps {
  recipe: Recipe | null;
  onToggle: () => void;
  onSave?: () => void;
  isSaving?: boolean;
  saveError?: string | null;
  isRecipeChanged?: boolean;
  onClearError?: () => void;
}

export default function RecipeDocument({
  recipe,
  onToggle,
  onSave,
  isSaving,
  saveError,
  isRecipeChanged,
  onClearError,
}: RecipeDocumentProps) {
  if (!recipe) return null;

  return (
    <div className="recipe-document h-full flex flex-col bg-surface">
      {/* Sticky Recipe Name with close button */}
      <div className="sticky top-0 bg-surface z-10 border-b border-accent/20 px-6 pt-6 pb-4 flex items-center justify-between gap-4">
        <h1
          className="text-xl font-bold text-text truncate"
          title={recipe.name || 'Untitled Recipe'}
        >
          {recipe.name || 'Untitled Recipe'}
        </h1>
        <button
          onClick={onToggle}
          className="md:hidden p-2 hover:bg-accent/10 rounded flex-shrink-0"
          aria-label="Close recipe"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Document content (scrollable) */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {/* Description */}
        {recipe.description && (
          <p className="text-text/80 text-base mb-6 leading-relaxed mt-4">
            {recipe.description}
          </p>
        )}

        {/* Metadata Row */}
        <div className="flex flex-wrap gap-4 mb-6 text-sm">
          {recipe.difficulty && (
            <div className="flex items-center gap-2">
              <span className="text-text/60">Difficulty:</span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
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
          )}
          {recipe.total_time_minutes && (
            <div className="flex items-center gap-2">
              <span className="text-text/60">Time:</span>
              <span className="text-text font-medium">
                {recipe.total_time_minutes} min
              </span>
            </div>
          )}
          {recipe.servings && (
            <div className="flex items-center gap-2">
              <span className="text-text/60">Servings:</span>
              <span className="text-text font-medium">{recipe.servings}</span>
            </div>
          )}
        </div>

        {/* Tags */}
        {recipe.tags && recipe.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            {recipe.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-accent/10 text-text/80 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Nutrition Section */}
        {recipe.nutrition && (
          <div className="mb-8">
            <SectionTitle>Nutrition</SectionTitle>
            <NutritionSection
              nutrition={recipe.nutrition}
              servings={recipe.servings}
            />
          </div>
        )}

        {/* Ingredients Section */}
        {recipe.ingredients && recipe.ingredients.length > 0 && (
          <div className="mb-8">
            <SectionTitle>Ingredients</SectionTitle>
            <ul className="space-y-2">
              {recipe.ingredients.map((ingredient, idx) => (
                <li key={idx} className="flex items-start gap-3 text-text/80">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span>
                    {ingredient.amount && (
                      <span className="font-medium">{ingredient.amount} </span>
                    )}
                    {ingredient.unit && (
                      <span className="text-text/60">{ingredient.unit} </span>
                    )}
                    <span>{ingredient.name}</span>
                    {ingredient.notes && (
                      <span className="text-text/60 text-sm italic">
                        {' '}
                        ({ingredient.notes})
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Instructions Section */}
        {recipe.steps && recipe.steps.length > 0 && (
          <div className="mb-8">
            <SectionTitle>Instructions</SectionTitle>
            <ol className="space-y-4">
              {recipe.steps.map((step, idx) => (
                <li key={idx} className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary text-sm font-medium rounded-full flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <div className="flex-1">
                    <p className="text-text/80 leading-relaxed">
                      {step.instruction}
                    </p>
                    {step.duration && (
                      <p className="text-text/60 text-sm mt-1 flex items-center gap-1">
                        <ClockIcon className="inline-block w-4 h-4" />{' '}
                        {step.duration} min
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Sticky footer with save button */}
      {onSave && (
        <div className="border-t border-accent/20 p-4">
          {saveError && (
            <div className="mb-3 p-2 bg-red-100 text-red-800 text-sm rounded flex items-center justify-between">
              <span>{saveError}</span>
              <button
                onClick={onClearError}
                className="ml-2 hover:opacity-70 text-lg leading-none"
              >
                ×
              </button>
            </div>
          )}
          <button
            onClick={onSave}
            disabled={!isRecipeChanged || isSaving}
            className="w-full px-4 py-3 bg-primary hover:bg-primary/90
                       disabled:bg-primary/50 disabled:cursor-not-allowed
                       text-white font-medium rounded-lg transition-colors
                       flex items-center justify-center gap-2"
          >
            {isSaving ? (
              <>
                <HourglassIcon className="animate-spin w-5 h-5" />
                Saving...
              </>
            ) : isRecipeChanged ? (
              <>
                <SaveIcon className="w-5 h-5" />
                Save Recipe
              </>
            ) : (
              <>
                <SaveIcon className="w-5 h-5" />
                Saved
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
