import type { RecipeNutrition } from '@/types/recipe';

interface NutritionSectionProps {
  nutrition: RecipeNutrition;
  servings?: number;
  className?: string;
}

export default function NutritionSection({
  nutrition,
  servings,
  className = '',
}: NutritionSectionProps) {
  const hasData =
    nutrition.calories ||
    nutrition.carbs ||
    nutrition.fats ||
    nutrition.proteins;

  if (!hasData) return null;

  return (
    <div className={className}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {nutrition.calories && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">
              {nutrition.calories}
            </div>
            <div className="text-xs text-text/60">cal</div>
          </div>
        )}
        {nutrition.proteins && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">
              {nutrition.proteins}g
            </div>
            <div className="text-xs text-text/60">Proteins</div>
          </div>
        )}
        {nutrition.carbs && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">
              {nutrition.carbs}g
            </div>
            <div className="text-xs text-text/60">Carbs</div>
          </div>
        )}
        {nutrition.fats && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">{nutrition.fats}g</div>
            <div className="text-xs text-text/60">Fats</div>
          </div>
        )}
      </div>
      {servings && servings > 1 && (
        <div className="mt-2 pt-2 text-xs text-text/50 text-center">
          <div className="flex flex-wrap justify-center gap-x-1 [&>span:not(:first-child)]:before:content-['·'] [&>span:not(:first-child)]:before:mr-1">
            {nutrition.calories && (
              <span className="whitespace-nowrap">
                {Math.round(nutrition.calories / servings)} cal
              </span>
            )}
            {nutrition.proteins && (
              <span className="whitespace-nowrap">
                {Math.round(nutrition.proteins / servings)}g proteins
              </span>
            )}
            {nutrition.carbs && (
              <span className="whitespace-nowrap">
                {Math.round(nutrition.carbs / servings)}g carbs
              </span>
            )}
            {nutrition.fats && (
              <span className="whitespace-nowrap">
                {Math.round(nutrition.fats / servings)}g fats
              </span>
            )}
          </div>
          <div className="mt-1">per serving</div>
        </div>
      )}
    </div>
  );
}
