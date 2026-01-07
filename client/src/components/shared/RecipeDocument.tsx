import type { RecipeContent } from '@/types/chat-message-types';

interface RecipeDocumentProps {
  recipe: RecipeContent | null;
  isVisible: boolean;
  onToggle: () => void;
}

export default function RecipeDocument({
  recipe,
  isVisible,
  onToggle,
}: RecipeDocumentProps) {
  if (!recipe) return null;

  return (
    <div className="recipe-document h-full flex flex-col bg-surface">
      {/* Header with toggle for mobile */}
      <div className="border-b border-accent/20 p-4 flex items-center justify-between">
        <h2 className="font-semibold text-lg text-text">Recipe</h2>
        <button
          onClick={onToggle}
          className="md:hidden p-2 hover:bg-accent/10 rounded"
          aria-label={isVisible ? 'Collapse recipe' : 'Expand recipe'}
        >
          {isVisible ? '▼' : '▶'}
        </button>
      </div>

      {/* Document content (always visible on desktop) */}
      <div
        className={`flex-1 overflow-y-auto p-6 ${isVisible ? 'block' : 'hidden md:block'}`}
      >
        {/* Recipe Name */}
        <h1 className="text-3xl font-bold text-text mb-2">
          {recipe.name || 'Untitled Recipe'}
        </h1>

        {/* Description */}
        {recipe.description && (
          <p className="text-text/80 text-base mb-6 leading-relaxed">
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

        {/* Ingredients Section */}
        {recipe.ingredients && recipe.ingredients.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-text mb-4 border-b border-accent/20 pb-2">
              Ingredients
            </h2>
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
            <h2 className="text-xl font-semibold text-text mb-4 border-b border-accent/20 pb-2">
              Instructions
            </h2>
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
                      <p className="text-text/60 text-sm mt-1">
                        ⏱️ {step.duration} min
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
