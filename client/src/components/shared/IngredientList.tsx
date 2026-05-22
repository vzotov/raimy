import type { RecipeIngredient } from '@/types/recipe';

interface IngredientListProps {
  ingredients: RecipeIngredient[];
}

function IngredientItem({ ingredient }: { ingredient: RecipeIngredient }) {
  return (
    <li className="flex items-start gap-3 text-text/80">
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
  );
}

export default function IngredientList({ ingredients }: IngredientListProps) {
  if (ingredients.length === 0) return null;

  const hasGroups = ingredients.some((i) => i.group != null);

  if (!hasGroups) {
    return (
      <ul className="space-y-2">
        {ingredients.map((ingredient) => (
          <IngredientItem key={ingredient.name} ingredient={ingredient} />
        ))}
      </ul>
    );
  }

  const groupOrder: string[] = [];
  const grouped: Record<string, RecipeIngredient[]> = {};
  const ungrouped: RecipeIngredient[] = [];

  for (const ingredient of ingredients) {
    if (ingredient.group) {
      if (!grouped[ingredient.group]) {
        groupOrder.push(ingredient.group);
        grouped[ingredient.group] = [];
      }
      grouped[ingredient.group].push(ingredient);
    } else {
      ungrouped.push(ingredient);
    }
  }

  return (
    <div>
      {groupOrder.map((groupName, i) => (
        <div key={groupName} className={i === 0 ? '' : 'mt-4'}>
          <p className="text-sm font-semibold text-text/60 uppercase tracking-wide mb-2">
            {groupName}
          </p>
          <ul className="space-y-2">
            {grouped[groupName].map((ingredient) => (
              <IngredientItem key={ingredient.name} ingredient={ingredient} />
            ))}
          </ul>
        </div>
      ))}
      {ungrouped.length > 0 && (
        <ul className="space-y-2 mt-4">
          {ungrouped.map((ingredient) => (
            <IngredientItem key={ingredient.name} ingredient={ingredient} />
          ))}
        </ul>
      )}
    </div>
  );
}
