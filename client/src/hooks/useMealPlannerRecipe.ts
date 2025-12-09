import { useCallback, useReducer } from 'react';
import type {
  ChatIngredient,
  RecipeContent,
  RecipeStep,
  RecipeUpdateContent,
} from '@/types/chat-message-types';

interface RecipeState {
  recipe: RecipeContent | null;
}

type RecipeAction =
  | { type: 'SET_RECIPE'; payload: RecipeContent }
  | {
      type: 'SET_METADATA';
      payload: {
        name: string;
        description?: string;
        difficulty?: string;
        total_time_minutes?: number;
        servings?: number;
        tags?: string[];
      };
    }
  | { type: 'SET_INGREDIENTS'; payload: ChatIngredient[] }
  | { type: 'SET_STEPS'; payload: RecipeStep[] }
  | { type: 'CLEAR_RECIPE' };

/**
 * Parse time string like "30 minutes", "1 hour", "1.5 hours" to minutes
 */
function parseTimeString(timeStr: string): number | undefined {
  if (!timeStr) return undefined;

  const lower = timeStr.toLowerCase();

  // Try to extract number
  const match = lower.match(/(\d+(?:\.\d+)?)/);
  if (!match) return undefined;

  const num = parseFloat(match[1]);

  // Check unit
  if (lower.includes('hour')) {
    return Math.round(num * 60);
  }
  if (lower.includes('min')) {
    return num;
  }

  // Default to minutes if no unit specified
  return num;
}

function recipeReducer(state: RecipeState, action: RecipeAction): RecipeState {
  switch (action.type) {
    case 'SET_RECIPE':
      return {
        ...state,
        recipe: action.payload,
      };

    case 'SET_METADATA': {
      // Initialize or update recipe with metadata
      const newRecipe: RecipeContent = {
        type: 'recipe',
        recipe_id: state.recipe?.recipe_id || '',
        name: action.payload.name,
        description: action.payload.description,
        difficulty: action.payload.difficulty,
        total_time_minutes: action.payload.total_time_minutes,
        servings: action.payload.servings,
        tags: action.payload.tags || [],
        ingredients: state.recipe?.ingredients || [],
        steps: state.recipe?.steps || [],
      };
      return { ...state, recipe: newRecipe };
    }

    case 'SET_INGREDIENTS': {
      if (!state.recipe) {
        // No recipe yet, just ignore ingredients
        return state;
      }
      return {
        ...state,
        recipe: {
          ...state.recipe,
          ingredients: action.payload,
        },
      };
    }

    case 'SET_STEPS': {
      if (!state.recipe) {
        // No recipe yet, just ignore steps
        return state;
      }
      return {
        ...state,
        recipe: {
          ...state.recipe,
          steps: action.payload,
        },
      };
    }

    case 'CLEAR_RECIPE':
      return {
        ...state,
        recipe: null,
      };

    default:
      return state;
  }
}

export function useMealPlannerRecipe(initialRecipe?: RecipeContent | null) {
  const [state, dispatch] = useReducer(recipeReducer, {
    recipe: initialRecipe || null,
  });

  const applyRecipeUpdate = useCallback(
    (update: RecipeUpdateContent) => {
      switch (update.action) {
        case 'set_metadata':
          dispatch({
            type: 'SET_METADATA',
            payload: {
              name: update.name,
              description: update.description,
              difficulty: update.difficulty,
              total_time_minutes:
                typeof update.total_time === 'string'
                  ? parseTimeString(update.total_time)
                  : undefined,
              servings:
                typeof update.servings === 'string'
                  ? parseInt(update.servings, 10) || undefined
                  : update.servings,
              tags: update.tags,
            },
          });
          break;

        case 'set_ingredients':
          dispatch({
            type: 'SET_INGREDIENTS',
            payload: update.ingredients,
          });
          break;

        case 'set_steps': {
          dispatch({
            type: 'SET_STEPS',
            payload: update.steps,
          });
          break;
        }
      }
    },
    [dispatch],
  );

  return {
    recipe: state.recipe,
    applyRecipeUpdate,
    clearRecipe: useCallback(
      () => dispatch({ type: 'CLEAR_RECIPE' }),
      [dispatch],
    ),
  };
}
