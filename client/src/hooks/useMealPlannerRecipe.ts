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

    case 'CLEAR_RECIPE':
      return {
        ...state,
        recipe: null,
      };

    default:
      return state;
  }
}

export function useMealPlannerRecipe(initialRecipe?: RecipeContent) {
  const [state, dispatch] = useReducer(recipeReducer, {
    recipe: initialRecipe || null,
  });

  const applyRecipeUpdate = useCallback(
    (update: RecipeUpdateContent) => {
      switch (update.action) {
        case 'set_metadata': {
          // Initialize or update recipe with metadata
          const newRecipe: RecipeContent = {
            type: 'recipe',
            recipe_id: state.recipe?.recipe_id || '',
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
            tags: update.tags || [],
            ingredients: state.recipe?.ingredients || [],
            steps: state.recipe?.steps || [],
          };
          dispatch({ type: 'SET_RECIPE', payload: newRecipe });
          break;
        }

        case 'set_ingredients': {
          if (!state.recipe) {
            // No recipe yet, just ignore ingredients
            // (agent should send set_metadata first)
            break;
          }
          dispatch({
            type: 'SET_RECIPE',
            payload: {
              ...state.recipe,
              ingredients: update.ingredients,
            },
          });
          break;
        }

        case 'set_steps': {
          if (!state.recipe) {
            // No recipe yet, just ignore steps
            break;
          }
          const formattedSteps: RecipeStep[] = update.steps.map((step, index) => ({
            step_number: index + 1,
            instruction: step,
          }));
          dispatch({
            type: 'SET_RECIPE',
            payload: {
              ...state.recipe,
              steps: formattedSteps,
            },
          });
          break;
        }
      }
    },
    [dispatch, state.recipe],
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
