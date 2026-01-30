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

  const perServing = servings && servings > 0 ? {
    calories: nutrition.calories ? Math.round(nutrition.calories / servings) : undefined,
    proteins: nutrition.proteins ? Math.round(nutrition.proteins / servings) : undefined,
    carbs: nutrition.carbs ? Math.round(nutrition.carbs / servings) : undefined,
    fats: nutrition.fats ? Math.round(nutrition.fats / servings) : undefined,
  } : nutrition;

  return (
    <div className={className}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {perServing.calories && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">
              {perServing.calories}
            </div>
            <div className="text-xs text-text/60">cal</div>
          </div>
        )}
        {perServing.proteins && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">
              {perServing.proteins}g
            </div>
            <div className="text-xs text-text/60">Proteins</div>
          </div>
        )}
        {perServing.carbs && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">
              {perServing.carbs}g
            </div>
            <div className="text-xs text-text/60">Carbs</div>
          </div>
        )}
        {perServing.fats && (
          <div className="text-center">
            <div className="text-xl font-bold text-text">{perServing.fats}g</div>
            <div className="text-xs text-text/60">Fats</div>
          </div>
        )}
      </div>
      {servings && servings > 1 && (
        <div className="mt-2 pt-2 text-xs text-text/50 text-center">
          <div className="flex flex-wrap justify-center gap-x-1 [&>span:not(:first-child)]:before:content-['·'] [&>span:not(:first-child)]:before:mr-1">
            {nutrition.calories && (
              <span className="whitespace-nowrap">
                {nutrition.calories} cal
              </span>
            )}
            {nutrition.proteins && (
              <span className="whitespace-nowrap">
                {nutrition.proteins}g proteins
              </span>
            )}
            {nutrition.carbs && (
              <span className="whitespace-nowrap">
                {nutrition.carbs}g carbs
              </span>
            )}
            {nutrition.fats && (
              <span className="whitespace-nowrap">
                {nutrition.fats}g fats
              </span>
            )}
          </div>
          <div className="mt-1">for {servings} servings</div>
        </div>
      )}
    </div>
  );
}
