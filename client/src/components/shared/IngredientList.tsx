import type { RecipeIngredient } from '@/types/recipe';

interface IngredientListProps {
  ingredients: RecipeIngredient[];
}

export default function IngredientList({ ingredients }: IngredientListProps) {
  if (ingredients.length === 0) return null;

  return (
    <ul className="space-y-2">
      {ingredients.map((ingredient) => (
        <li
          key={ingredient.name}
          className="flex items-start gap-3 text-text/80"
        >
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
  );
}
