import { useCallback, useReducer } from 'react';
import type {
  ChatIngredient,
  RecipeContent,
  RecipeStep,
  RecipeUpdateContent,
} from '@/types/chat-message-types';

interface RecipeState {
  recipe: RecipeContent | null;
  isVisible: boolean; // For mobile expandable panel
}

type RecipeAction =
  | { type: 'SET_RECIPE'; payload: RecipeContent }
  | { type: 'UPDATE_METADATA'; payload: Partial<RecipeContent> }
  | { type: 'ADD_INGREDIENT'; payload: ChatIngredient }
  | { type: 'REMOVE_INGREDIENT'; payload: number }
  | {
      type: 'UPDATE_INGREDIENT';
      payload: { index: number; ingredient: ChatIngredient };
    }
  | { type: 'ADD_STEP'; payload: RecipeStep }
  | { type: 'REMOVE_STEP'; payload: number }
  | { type: 'UPDATE_STEP'; payload: { stepNumber: number; step: RecipeStep } }
  | { type: 'TOGGLE_VISIBILITY' }
  | { type: 'CLEAR_RECIPE' };

function recipeReducer(state: RecipeState, action: RecipeAction): RecipeState {
  switch (action.type) {
    case 'SET_RECIPE':
      return {
        ...state,
        recipe: action.payload,
      };

    case 'UPDATE_METADATA':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          ...action.payload,
        },
      };

    case 'ADD_INGREDIENT':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          ingredients: [...state.recipe.ingredients, action.payload],
        },
      };

    case 'REMOVE_INGREDIENT':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          ingredients: state.recipe.ingredients.filter(
            (_, idx) => idx !== action.payload,
          ),
        },
      };

    case 'UPDATE_INGREDIENT':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          ingredients: state.recipe.ingredients.map((ing, idx) =>
            idx === action.payload.index ? action.payload.ingredient : ing,
          ),
        },
      };

    case 'ADD_STEP':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          steps: [...state.recipe.steps, action.payload],
        },
      };

    case 'REMOVE_STEP':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          steps: state.recipe.steps.filter(
            (step) => step.step_number !== action.payload,
          ),
        },
      };

    case 'UPDATE_STEP':
      if (!state.recipe) return state;
      return {
        ...state,
        recipe: {
          ...state.recipe,
          steps: state.recipe.steps.map((step) =>
            step.step_number === action.payload.stepNumber
              ? action.payload.step
              : step,
          ),
        },
      };

    case 'TOGGLE_VISIBILITY':
      return {
        ...state,
        isVisible: !state.isVisible,
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
    isVisible: false,
  });

  const applyRecipeUpdate = useCallback(
    (update: RecipeUpdateContent) => {
      switch (update.action) {
        case 'set':
          // Full recipe - convert RecipeUpdateContent to RecipeContent
          if (
            update.name &&
            update.ingredients &&
            update.steps &&
            update.recipe_id
          ) {
            dispatch({
              type: 'SET_RECIPE',
              payload: {
                type: 'recipe',
                recipe_id: update.recipe_id,
                name: update.name,
                description: update.description,
                ingredients: update.ingredients,
                steps: update.steps,
                total_time_minutes: update.total_time_minutes,
                difficulty: update.difficulty,
                servings: update.servings,
                tags: update.tags,
              },
            });
          }
          break;

        case 'update_metadata':
          dispatch({
            type: 'UPDATE_METADATA',
            payload: {
              name: update.name,
              description: update.description,
              difficulty: update.difficulty,
              total_time_minutes: update.total_time_minutes,
              servings: update.servings,
              tags: update.tags,
            },
          });
          break;

        case 'set_metadata':
          // NEW: Bulk metadata update - replace all metadata fields
          if (!state.recipe) break;
          dispatch({
            type: 'SET_RECIPE',
            payload: {
              ...state.recipe,
              name: update.name || state.recipe.name,
              description: update.description,
              difficulty: update.difficulty,
              total_time_minutes: update.total_time_minutes,
              servings: typeof update.servings === 'string' ? parseInt(update.servings) || 0 : update.servings,
              tags: update.tags,
            },
          });
          break;

        case 'set_ingredients':
          // NEW: Replace entire ingredients array
          if (!state.recipe) break;
          dispatch({
            type: 'SET_RECIPE',
            payload: {
              ...state.recipe,
              ingredients: update.ingredients || [],
            },
          });
          break;

        case 'set_steps':
          // NEW: Replace entire steps array (supports both string[] and RecipeStep[])
          if (!state.recipe) break;
          const steps = update.steps || [];
          // Convert string steps to RecipeStep format
          const formattedSteps = steps.map((step, index) => {
            if (typeof step === 'string') {
              return {
                step_number: index + 1,
                instruction: step,
              };
            }
            return step;
          });
          dispatch({
            type: 'SET_RECIPE',
            payload: {
              ...state.recipe,
              steps: formattedSteps,
            },
          });
          break;

        case 'add_ingredient':
          if (update.ingredient) {
            dispatch({
              type: 'ADD_INGREDIENT',
              payload: update.ingredient,
            });
          }
          break;

        case 'remove_ingredient':
          if (update.ingredient_index !== undefined) {
            dispatch({
              type: 'REMOVE_INGREDIENT',
              payload: update.ingredient_index,
            });
          }
          break;

        case 'update_ingredient':
          if (
            update.ingredient_index !== undefined &&
            update.ingredient
          ) {
            dispatch({
              type: 'UPDATE_INGREDIENT',
              payload: {
                index: update.ingredient_index,
                ingredient: update.ingredient,
              },
            });
          }
          break;

        case 'add_step':
          if (update.step) {
            dispatch({
              type: 'ADD_STEP',
              payload: update.step,
            });
          }
          break;

        case 'remove_step':
          if (update.step_number !== undefined) {
            dispatch({
              type: 'REMOVE_STEP',
              payload: update.step_number,
            });
          }
          break;

        case 'update_step':
          if (update.step_number !== undefined && update.step) {
            dispatch({
              type: 'UPDATE_STEP',
              payload: {
                stepNumber: update.step_number,
                step: update.step,
              },
            });
          }
          break;
      }
    },
    [dispatch],
  );

  return {
    recipe: state.recipe,
    isVisible: state.isVisible,
    applyRecipeUpdate,
    toggleVisibility: useCallback(
      () => dispatch({ type: 'TOGGLE_VISIBILITY' }),
      [dispatch],
    ),
    clearRecipe: useCallback(
      () => dispatch({ type: 'CLEAR_RECIPE' }),
      [dispatch],
    ),
  };
}
