'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { mealPlannerSessions } from '@/lib/api';
import classNames from 'classnames';

export default function NewMealPlanner() {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleSend = async () => {
    if (!message.trim() || isCreating) return;

    try {
      setIsCreating(true);

      // Create the session with the initial message
      const response = await mealPlannerSessions.create(message.trim());

      if (response.error) {
        console.error('Failed to create session:', response.error);
        setIsCreating(false);
        return;
      }

      if (response.data) {
        const sessionId = response.data.session.id;

        // Redirect to the session page
        // The initial message is already saved in the database
        router.push(`/meal-planner/${sessionId}`);
      }
    } catch (error) {
      console.error('Error creating session:', error);
      setIsCreating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-full max-w-3xl">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-text mb-3">Meal Planner</h1>
            <p className="text-lg text-text/70">
              What would you like help with today?
            </p>
          </div>

          {/* Input Area */}
          <div className="bg-surface border border-accent/20 rounded-2xl shadow-lg p-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isCreating}
              placeholder="Ask about meal ideas, recipes, ingredients, or dietary preferences..."
              className={classNames(
                'w-full px-4 py-3 bg-transparent text-text resize-none',
                'focus:outline-none placeholder:text-text/40',
                'min-h-[120px] max-h-[300px]'
              )}
              autoFocus
            />

            <div className="flex items-center justify-between pt-3 border-t border-accent/10">
              <div className="text-xs text-text/50">
                Press Enter to send, Shift+Enter for new line
              </div>

              <button
                onClick={handleSend}
                disabled={!message.trim() || isCreating}
                className={classNames(
                  'px-6 py-2.5 rounded-lg font-medium transition-all',
                  {
                    'bg-primary text-white hover:bg-primary/90 hover:shadow-lg':
                      message.trim() && !isCreating,
                    'bg-accent/20 text-text/30 cursor-not-allowed':
                      !message.trim() || isCreating,
                  }
                )}
              >
                {isCreating ? 'Starting chat...' : 'Start Chat'}
              </button>
            </div>
          </div>

          {/* Example prompts */}
          <div className="mt-8 space-y-3">
            <p className="text-sm text-text/50 font-medium">Try asking:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                'Plan a week of healthy dinners',
                'Quick breakfast ideas under 10 minutes',
                'Vegetarian recipes with high protein',
                'What can I make with chicken and rice?',
              ].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => setMessage(example)}
                  disabled={isCreating}
                  className={classNames(
                    'text-left px-4 py-3 rounded-lg border border-accent/20',
                    'hover:border-primary/50 hover:bg-accent/5 transition-colors',
                    'text-sm text-text/70',
                    {
                      'cursor-not-allowed opacity-50': isCreating,
                    }
                  )}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
