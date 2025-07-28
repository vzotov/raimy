'use client';

import { useState } from 'react';

interface CreateFakeRecipeButtonProps {
  userId?: string;
  onRecipeCreated: () => void;
}

export default function CreateFakeRecipeButton({ userId = "anonymous", onRecipeCreated }: CreateFakeRecipeButtonProps) {
  const [creatingFakeRecipe, setCreatingFakeRecipe] = useState(false);

  const createFakeRecipe = async () => {
    try {
      setCreatingFakeRecipe(true);
      
      const fakeRecipe = {
        name: "Grilled Chicken with Vegetables",
        description: "A healthy and delicious grilled chicken dish with fresh vegetables. Perfect for a quick weeknight dinner.",
        ingredients: [
          "2 boneless, skinless chicken breasts",
          "1 red bell pepper, sliced",
          "1 yellow bell pepper, sliced",
          "1 zucchini, sliced",
          "2 tablespoons olive oil",
          "1 teaspoon dried oregano",
          "1 teaspoon dried basil",
          "Salt and pepper to taste",
          "1 lemon, sliced"
        ],
        steps: [
          {
            instruction: "Preheat grill to medium-high heat",
            duration_minutes: 5
          },
          {
            instruction: "Season chicken breasts with salt, pepper, oregano, and basil",
            duration_minutes: 2
          },
          {
            instruction: "Brush vegetables with olive oil and season with salt and pepper",
            duration_minutes: 3
          },
          {
            instruction: "Grill chicken for 6-8 minutes per side until internal temperature reaches 165°F",
            duration_minutes: 16
          },
          {
            instruction: "Grill vegetables for 8-10 minutes, turning occasionally",
            duration_minutes: 10
          },
          {
            instruction: "Let chicken rest for 5 minutes before slicing",
            duration_minutes: 5
          }
        ],
        total_time_minutes: 41,
        difficulty: "medium",
        servings: 2,
        tags: ["grilled", "healthy", "chicken", "vegetables", "quick-meal"],
        user_id: userId
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/recipes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(fakeRecipe),
      });

      if (!response.ok) {
        throw new Error(`Failed to create fake recipe: ${response.status}`);
      }

      const result = await response.json();
      console.log('Fake recipe created:', result);
      
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
      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
    >
      {creatingFakeRecipe ? 'Creating...' : 'Create Fake Recipe'}
    </button>
  );
} 