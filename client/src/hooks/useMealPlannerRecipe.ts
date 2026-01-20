import { useCallback, useReducer } from 'react';
import type { RecipeUpdateContent } from '@/types/chat-message-types';
import type {
  Recipe,
  RecipeIngredient,
  RecipeNutrition,
  RecipeStep,
} from '@/types/recipe';

interface RecipeState {
  recipe: Recipe | null;
  isRecipeChanged: boolean;
}

type RecipeAction =
  | { type: 'SET_RECIPE'; payload: Recipe }
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
  | { type: 'SET_INGREDIENTS'; payload: RecipeIngredient[] }
  | { type: 'SET_STEPS'; payload: RecipeStep[] }
  | { type: 'SET_NUTRITION'; payload: RecipeNutrition }
  | { type: 'RESET_CHANGED_FLAG' }
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

function createEmptyRecipe(): Recipe {
  return {
    id: '',
    name: '',
    ingredients: [],
    steps: [],
  };
}

function recipeReducer(state: RecipeState, action: RecipeAction): RecipeState {
  switch (action.type) {
    case 'SET_RECIPE':
      return {
        ...state,
        recipe: action.payload,
      };

    case 'SET_METADATA': {
      const baseRecipe = state.recipe || createEmptyRecipe();
      return {
        ...state,
        recipe: {
          ...baseRecipe,
          ...action.payload,
          updated_at: state.recipe ? new Date().toISOString() : undefined,
        },
        isRecipeChanged: true,
      };
    }

    case 'SET_INGREDIENTS': {
      const baseRecipe = state.recipe || createEmptyRecipe();
      return {
        ...state,
        recipe: {
          ...baseRecipe,
          ingredients: action.payload,
        },
        isRecipeChanged: true,
      };
    }

    case 'SET_STEPS': {
      const baseRecipe = state.recipe || createEmptyRecipe();
      return {
        ...state,
        recipe: {
          ...baseRecipe,
          steps: action.payload,
        },
        isRecipeChanged: true,
      };
    }

    case 'SET_NUTRITION': {
      const baseRecipe = state.recipe || createEmptyRecipe();
      return {
        ...state,
        recipe: {
          ...baseRecipe,
          nutrition: action.payload,
        },
        isRecipeChanged: true,
      };
    }

    case 'RESET_CHANGED_FLAG':
      return {
        ...state,
        isRecipeChanged: false,
      };

    case 'CLEAR_RECIPE':
      return {
        ...state,
        recipe: null,
        isRecipeChanged: false,
      };

    default:
      return state;
  }
}

export function useMealPlannerRecipe(
  initialRecipe?: Recipe | null,
  initialIsChanged?: boolean,
) {
  const [state, dispatch] = useReducer(recipeReducer, {
    recipe: initialRecipe || null,
    isRecipeChanged: initialIsChanged ?? false,
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

        case 'set_nutrition': {
          dispatch({
            type: 'SET_NUTRITION',
            payload: update.nutrition,
          });
          break;
        }
      }
    },
    [dispatch],
  );

  return {
    recipe: state.recipe,
    isRecipeChanged: state.isRecipeChanged,
    applyRecipeUpdate,
    setRecipe: useCallback(
      (recipe: Recipe) => dispatch({ type: 'SET_RECIPE', payload: recipe }),
      [dispatch],
    ),
    resetChangedFlag: useCallback(
      () => dispatch({ type: 'RESET_CHANGED_FLAG' }),
      [dispatch],
    ),
    clearRecipe: useCallback(
      () => dispatch({ type: 'CLEAR_RECIPE' }),
      [dispatch],
    ),
  };
}
