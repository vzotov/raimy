'use client';

import { useState } from 'react';
import { post } from '@/lib/api';

interface CreateFakeRecipeButtonProps {
  onRecipeCreated: () => void;
}

export default function CreateFakeRecipeButton({
  onRecipeCreated,
}: CreateFakeRecipeButtonProps) {
  const [creatingFakeRecipe, setCreatingFakeRecipe] = useState(false);

  const createFakeRecipe = async () => {
    try {
      setCreatingFakeRecipe(true);

      const fakeRecipe = {
        name: 'Grilled Chicken with Vegetables',
        description:
          'A healthy and delicious grilled chicken dish with fresh vegetables. Perfect for a quick weeknight dinner.',
        ingredients: [
          '2 boneless, skinless chicken breasts',
          '1 red bell pepper, sliced',
          '1 yellow bell pepper, sliced',
          '1 zucchini, sliced',
          '2 tablespoons olive oil',
          '1 teaspoon dried oregano',
          '1 teaspoon dried basil',
          'Salt and pepper to taste',
          '1 lemon, sliced',
        ],
        steps: [
          {
            instruction: 'Preheat grill to medium-high heat',
            duration_minutes: 5,
          },
          {
            instruction:
              'Season chicken breasts with salt, pepper, oregano, and basil',
            duration_minutes: 2,
          },
          {
            instruction:
              'Brush vegetables with olive oil and season with salt and pepper',
            duration_minutes: 3,
          },
          {
            instruction:
              'Grill chicken for 6-8 minutes per side until internal temperature reaches 165°F',
            duration_minutes: 16,
          },
          {
            instruction:
              'Grill vegetables for 8-10 minutes, turning occasionally',
            duration_minutes: 10,
          },
          {
            instruction: 'Let chicken rest for 5 minutes before slicing',
            duration_minutes: 5,
          },
        ],
        total_time_minutes: 41,
        difficulty: 'medium',
        servings: 2,
        tags: ['grilled', 'healthy', 'chicken', 'vegetables', 'quick-meal'],
      };

      const result = await post('/api/recipes', fakeRecipe);

      if (result.error) {
        throw new Error(result.error);
      }

      console.log('Fake recipe created:', result.data);

      // Notify parent component to refresh recipes
      onRecipeCreated();
    } catch (err) {
      console.error('Error creating fake recipe:', err);
      // You could add a toast notification here if needed
    } finally {
      setCreatingFakeRecipe(false);
    }
  };

  return (
    <button
      onClick={createFakeRecipe}
      disabled={creatingFakeRecipe}
      className="px-4 py-2 bg-accent2 text-text rounded-lg hover:bg-accent2/80 disabled:bg-surface/50 disabled:cursor-not-allowed transition-colors"
    >
      {creatingFakeRecipe ? 'Creating...' : 'Create Fake Recipe'}
    </button>
  );
}
