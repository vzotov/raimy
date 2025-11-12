import { ChefHatIcon } from '@/components/icons';
import React, { useState } from 'react';
import { Timer } from '@/components/shared/TimerList';
import { Ingredient } from '@/components/shared/IngredientList';

interface KitchenDebugPanelProps {
  connectionState: string;
  assistantState: string;
  onSetIngredients: (ingredients: Ingredient[]) => void;
  onSetTimers: (timers: Timer[]) => void;
  onSetUserMessage: (message: string) => void;
  onSetRecipeName: (name: string) => void;
}

export default function KitchenDebugPanel({
  connectionState,
  assistantState,
  onSetIngredients,
  onSetTimers,
  onSetUserMessage,
  onSetRecipeName,
}: KitchenDebugPanelProps) {
  const [isVisible, setIsVisible] = useState(false);

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
  };

  // Mock functions
  const addMockIngredients = () => {
    const mockIngredients = [
      { id: '1', name: 'pasta', amount: '200', unit: 'g' },
      { id: '2', name: 'eggs', amount: '2', unit: 'pieces' },
      { id: '3', name: 'bacon', amount: '100', unit: 'g' },
      { id: '4', name: 'parmesan cheese', amount: '50', unit: 'g' },
      { id: '5', name: 'black pepper', amount: '1', unit: 'tsp' },
      { id: '6', name: 'salt', amount: '1', unit: 'tsp' },
      { id: '7', name: 'olive oil', amount: '2', unit: 'tbsp' },
      { id: '8', name: 'garlic', amount: '2', unit: 'cloves' },
      { id: '9', name: 'onion', amount: '1', unit: 'medium' },
      { id: '10', name: 'tomatoes', amount: '4', unit: 'pieces' },
      { id: '11', name: 'basil', amount: '1/4', unit: 'cup' },
      { id: '12', name: 'oregano', amount: '1', unit: 'tsp' },
      { id: '13', name: 'red pepper flakes', amount: '1/2', unit: 'tsp' },
      { id: '14', name: 'lemon juice', amount: '1', unit: 'tbsp' },
      { id: '15', name: 'butter', amount: '2', unit: 'tbsp' },
    ];
    onSetIngredients(mockIngredients);
  };

  const updateIngredients = () => {
    const updatedIngredients = [
      { id: '1', name: 'pasta', amount: '200', unit: 'g', highlighted: true },
      { id: '2', name: 'eggs', amount: '2', unit: 'pieces', highlighted: true },
      { id: '3', name: 'bacon', amount: '100', unit: 'g' },
      { id: '4', name: 'parmesan cheese', amount: '50', unit: 'g', highlighted: true },
      { id: '5', name: 'black pepper', amount: '1', unit: 'tsp' },
      { id: '6', name: 'salt', amount: '1', unit: 'tsp', used: true },
      { id: '7', name: 'olive oil', amount: '2', unit: 'tbsp' },
      { id: '8', name: 'garlic', amount: '2', unit: 'cloves' },
      { id: '9', name: 'onion', amount: '1', unit: 'medium' },
      { id: '10', name: 'tomatoes', amount: '4', unit: 'pieces' },
      { id: '11', name: 'basil', amount: '1/4', unit: 'cup' },
      { id: '12', name: 'oregano', amount: '1', unit: 'tsp' },
      { id: '13', name: 'red pepper flakes', amount: '1/2', unit: 'tsp' },
      { id: '14', name: 'lemon juice', amount: '1', unit: 'tbsp' },
      { id: '15', name: 'butter', amount: '2', unit: 'tbsp', used: true },
    ];
    onSetIngredients(updatedIngredients);
  };

  const addMockTimers = () => {
    const mockTimerData = [
      {
        duration: 600, // 10 minutes
        label: 'for pasta to cook',
        startedAt: Date.now() - 120000 // started 2 minutes ago
      },
      {
        duration: 300, // 5 minutes
        label: 'for sauce to simmer',
        startedAt: Date.now() - 60000 // started 1 minute ago
      }
    ];
    onSetTimers(mockTimerData);
  };

  const setMockUserMessage = () => {
    onSetUserMessage('How long should I cook the pasta for?');
  };

  const setMockRecipeName = () => {
    onSetRecipeName('Spaghetti Carbonara');
  };

  const clearAll = () => {
    onSetIngredients([]);
    onSetTimers([]);
    onSetUserMessage('');
    onSetRecipeName('');
  };
  return (
    <>
      {/* Toggle button when panel is hidden */}
      {!isVisible && (
        <button
          onClick={toggleVisibility}
          className="absolute bottom-4 left-4 w-8 h-8 bg-surface border border-accent2/20 rounded-lg shadow-lg flex items-center justify-center text-xs font-semibold text-text/70 hover:bg-accent2/10 transition-colors z-50"
          title="Show Debug Panel"
        >
          <ChefHatIcon className="w-4 h-4" />
        </button>
      )}

      {/* Debug Panel when visible */}
      {isVisible && (
        <div className="absolute bottom-4 left-4 bg-surface border border-accent2/20 rounded-lg p-3 shadow-lg z-50">
          {/* Header with title, toggle button, and indicators */}
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-semibold text-text/70">Debug Panel</div>
            <div className="flex items-center space-x-2">
              {/* Debug indicators */}
              <div className="flex space-x-1">
                <div
                  className={`h-2 w-2 rounded-full ${connectionState === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}
                  title={connectionState}
                ></div>
                <div className="h-2 w-2 rounded-full bg-primary" title={assistantState}></div>
              </div>
              {/* Toggle button */}
              <button
                onClick={toggleVisibility}
                className="w-5 h-5 bg-accent2/20 rounded flex items-center justify-center text-xs font-semibold text-text/70 hover:bg-accent2/30 transition-colors"
                title="Hide Debug Panel"
              >
                ×
              </button>
            </div>
          </div>

          {/* Debug buttons */}
          <div className="flex flex-col gap-2">
            <button
              onClick={addMockIngredients}
              className="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-hover transition-colors"
            >
              Add Ingredients
            </button>
            <button
              onClick={updateIngredients}
              className="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-hover transition-colors"
            >
              Update Ingredients
            </button>
            <button
              onClick={addMockTimers}
              className="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-hover transition-colors"
            >
              Add Timers
            </button>
            <button
              onClick={setMockUserMessage}
              className="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-hover transition-colors"
            >
              Set User Message
            </button>
            <button
              onClick={setMockRecipeName}
              className="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-hover transition-colors"
            >
              Set Recipe Name
            </button>
            <button
              onClick={clearAll}
              className="px-3 py-1 text-xs bg-danger text-white rounded hover:bg-danger-hover transition-colors"
            >
              Clear All
            </button>
          </div>
        </div>
      )}
    </>
  );
}
