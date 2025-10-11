/**
 * Base ingredient type shared across the application.
 * Extended by specific components for their use cases.
 */
export interface BaseIngredient {
  name: string;
  amount?: string;
  unit?: string;
}