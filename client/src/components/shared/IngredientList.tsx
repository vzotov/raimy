import type { BaseIngredient } from '@/types/ingredient';
import ScrollableArea from './ScrollableArea';

/**
 * Kitchen ingredient extends base with UI state for highlighting and tracking usage
 */
export interface Ingredient extends BaseIngredient {
  highlighted?: boolean;
  used?: boolean;
}

interface IngredientListProps {
  ingredients: Ingredient[];
}

export default function IngredientList({ ingredients }: IngredientListProps) {
  if (ingredients.length === 0) return null;

  // Sort ingredients: highlighted first, then normal, then used at bottom
  const sortedIngredients = [...ingredients].sort((a, b) => {
    // Highlighted items first
    if (a.highlighted && !b.highlighted) return -1;
    if (!a.highlighted && b.highlighted) return 1;

    // Used items last
    if (a.used && !b.used) return 1;
    if (!a.used && b.used) return -1;

    return 0; // Maintain original order within each group
  });

  return (
    <ScrollableArea className="flex flex-1 items-stretch flex-col min-h-0">
      <ul className="space-y-2 list-disc pl-4">
        {sortedIngredients.map((ingredient) => (
          <li
            key={ingredient.name}
            className={`text-lg leading-relaxed mb-0 ${
              ingredient.highlighted
                ? 'text-primary font-semibold [li::marker]:text-primary'
                : ingredient.used
                  ? 'text-text/40 line-through [li::marker]:text-text/40'
                  : 'text-text/75 font-normal'
            }`}
          >
            {ingredient.amount && `${ingredient.amount} `}
            {ingredient.unit && `${ingredient.unit} `}
            {ingredient.name}
          </li>
        ))}
      </ul>
    </ScrollableArea>
  );
}
