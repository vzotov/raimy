import { useCallback, useReducer } from 'react';
import type { RecipeUpdateContent } from '@/types/chat-message-types';
import type { Recipe, RecipeIngredient, RecipeStep } from '@/types/recipe';

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

function recipeReducer(state: RecipeState, action: RecipeAction): RecipeState {
  switch (action.type) {
    case 'SET_RECIPE':
      return {
        ...state,
        recipe: action.payload,
      };

    case 'SET_METADATA': {
      if (!state.recipe) {
        // Create new recipe during initial creation
        const newRecipe: Recipe = {
          id: '',
          name: action.payload.name,
          description: action.payload.description,
          total_time_minutes: action.payload.total_time_minutes,
          difficulty: action.payload.difficulty,
          servings: action.payload.servings,
          tags: action.payload.tags,
          ingredients: [],
          steps: [],
          user_id: undefined,
          chat_session_id: undefined,
          created_at: undefined,
          updated_at: undefined,
        };
        return { ...state, recipe: newRecipe, isRecipeChanged: true };
      }

      // Update existing recipe
      return {
        ...state,
        recipe: {
          ...state.recipe,
          ...action.payload,
          updated_at: new Date().toISOString(),
        },
        isRecipeChanged: true,
      };
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
        isRecipeChanged: true,
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

export function useMealPlannerRecipe(initialRecipe?: Recipe | null) {
  // Determine initial state: if recipe exists but has no id, it's unsaved
  const initialIsRecipeChanged = !!(initialRecipe && !initialRecipe.id);

  const [state, dispatch] = useReducer(recipeReducer, {
    recipe: initialRecipe || null,
    isRecipeChanged: initialIsRecipeChanged,
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
