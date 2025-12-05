import { chatReducer } from './chatReducer';
import type { KitchenMessageAction, KitchenMessageState } from './types';

/**
 * Kitchen-specific reducer that extends base chat reducer
 */
export function kitchenMessageReducer(
	state: KitchenMessageState,
	action: KitchenMessageAction,
): KitchenMessageState {
	// Handle kitchen-specific actions
	switch (action.type) {
		case 'SET_INGREDIENTS':
			return { ...state, ingredients: action.payload };

		case 'UPDATE_INGREDIENTS': {
			// Payload contains partial updates, merge with existing
			const updatedIngredients = state.ingredients.map((ing) => {
				const update = action.payload.find((u) => u.name === ing.name);
				return update ? { ...ing, ...update } : ing;
			});
			return { ...state, ingredients: updatedIngredients };
		}

		case 'ADD_TIMER':
			return { ...state, timers: [...state.timers, action.payload] };

		default:
			// Delegate to base chat reducer for common actions
			return {
				...state,
				...chatReducer(state, action),
			};
	}
}
