'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { kitchenSessions } from '@/lib/api';
import classNames from 'classnames';

export default function KitchenPage() {
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartCooking = async () => {
    try {
      setIsCreating(true);
      setError(null);

      const response = await kitchenSessions.create();

      if (response.error) {
        setError(response.error);
        setIsCreating(false);
        return;
      }

      if (response.data?.session?.id) {
        router.push(`/kitchen/${response.data.session.id}`);
      }
    } catch (err) {
      console.error('Failed to create kitchen session:', err);
      setError('Failed to create session. Please try again.');
      setIsCreating(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">👨‍🍳</div>
        <h1 className="text-4xl font-bold text-text mb-3">Kitchen</h1>
        <p className="text-lg text-text/70 mb-6">
          Get step-by-step guidance while you cook with real-time assistance
        </p>

        <button
          onClick={handleStartCooking}
          disabled={isCreating}
          className={classNames(
            'px-8 py-3 rounded-lg font-medium transition-all text-lg',
            {
              'bg-primary text-white hover:bg-primary/90': !isCreating,
              'bg-accent/20 text-text/30 cursor-not-allowed': isCreating,
            }
          )}
        >
          {isCreating ? 'Starting...' : 'Start Cooking'}
        </button>

        {error && (
          <div className="mt-4 bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-500 text-sm">
            {error}
          </div>
        )}

        <div className="mt-8 text-sm text-text/50">
          Select a previous session from the menu or start a new one
        </div>
      </div>
    </div>
  );
}
