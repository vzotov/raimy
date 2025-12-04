'use client';

import classNames from 'classnames';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { mealPlannerSessions } from '@/lib/api';

export default function MealPlannerPage() {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message || isCreating) return;

    try {
      setIsCreating(true);
      setError(null);

      const response = await mealPlannerSessions.create(message.trim());

      if (response.error) {
        setError(response.error);
        setIsCreating(false);
        return;
      }

      if (response.data?.session?.id) {
        router.push(`/meal-planner/${response.data.session.id}`);
      }
    } catch (err) {
      console.error('Failed to create session:', err);
      setError('Failed to create session. Please try again.');
      setIsCreating(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-text mb-3">Meal Planner</h1>
          <p className="text-lg text-text/70">
            Start planning your meals with AI assistance
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-surface border border-accent/20 rounded-2xl shadow-lg p-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value.trim())}
              disabled={isCreating}
              placeholder="What would you like help with today? (e.g., 'Plan a week of healthy dinners')"
              className={classNames(
                'w-full px-4 py-3 bg-transparent text-text resize-none',
                'focus:outline-none placeholder:text-text/40',
                'min-h-[120px]',
              )}
              autoFocus
            />

            <div className="flex items-center justify-between pt-3 border-t border-accent/10">
              <div className="text-xs text-text/50">
                {message.length === 0 && 'Start typing to begin...'}
              </div>

              <button
                type="submit"
                disabled={!message || isCreating}
                className={classNames(
                  'px-6 py-2.5 rounded-lg font-medium transition-all',
                  {
                    'bg-primary text-white hover:bg-primary/90':
                      message && !isCreating,
                    'bg-accent/20 text-text/30 cursor-not-allowed':
                      !message || isCreating,
                  },
                )}
              >
                {isCreating ? 'Creating...' : 'Start Chat'}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-500 text-sm">
              {error}
            </div>
          )}
        </form>

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
                type="button"
                onClick={() => setMessage(example)}
                disabled={isCreating}
                className={classNames(
                  'text-left px-4 py-3 rounded-lg border border-accent/20',
                  'hover:border-primary/50 hover:bg-accent/5 transition-colors',
                  'text-sm text-text/70',
                  {
                    'cursor-not-allowed opacity-50': isCreating,
                  },
                )}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
