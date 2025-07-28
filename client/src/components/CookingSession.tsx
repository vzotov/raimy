'use client';

import { useState, useEffect } from 'react';
import { useSSE } from '@/hooks/useSSE';

interface Timer {
  duration: number;
  label: string;
  started_at: number;
}

interface CookingSessionProps {
  className?: string;
}

export const CookingSession = ({ className = '' }: CookingSessionProps) => {
  const [currentTimer, setCurrentTimer] = useState<Timer | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [recipeName, setRecipeName] = useState<string>('');

  const { isConnected, lastEvent, sendEvent } = useSSE({
    onMessage: (event) => {
      console.log('Received cooking event:', event);
      
      switch (event.type) {
        case 'session_started':
          setSessionId(event.data.session_id);
          setRecipeName(event.data.recipe_name);
          break;
        case 'timer_set':
          setCurrentTimer(event.data);
          break;
        case 'recipe_completed':
          setCurrentTimer(null);
          setSessionId(null);
          setRecipeName('');
          break;
      }
    },
    onError: (error) => {
      console.error('SSE connection error:', error);
    },
  });

  const handleStartRecipe = async () => {
    try {
      await sendEvent('recipes/start', {
        name: 'Grilled Steak',
        instructions: [
          'Preheat grill to high heat',
          'Season steak with salt and pepper',
          'Cook for 4 minutes per side',
          'Let rest for 5 minutes'
        ]
      });
    } catch (error) {
      console.error('Failed to start recipe:', error);
    }
  };

  const handleSetTimer = async () => {
    try {
      await sendEvent('timers/set', {
        duration: 240, // 4 minutes
        label: 'to flip the steak'
      });
    } catch (error) {
      console.error('Failed to set timer:', error);
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getTimerRemaining = (timer: Timer) => {
    const elapsed = Math.floor((Date.now() / 1000) - timer.started_at);
    const remaining = Math.max(0, timer.duration - elapsed);
    return remaining;
  };

  return (
    <div className={`p-6 bg-white rounded-lg shadow-md ${className}`}>
      <h2 className="text-2xl font-bold mb-4">Cooking Session</h2>
      
      {/* Connection Status */}
      <div className="mb-4">
        <span className={`inline-block w-3 h-3 rounded-full mr-2 ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`}></span>
        <span className="text-sm">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Session Info */}
      {sessionId && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900">Active Session</h3>
          <p className="text-blue-700">Recipe: {recipeName}</p>
          <p className="text-blue-700">Session ID: {sessionId}</p>
        </div>
      )}

      {/* Current Timer */}
      {currentTimer && (
        <div className="mb-4 p-4 bg-yellow-50 rounded-lg">
          <h3 className="font-semibold text-yellow-900">Current Timer</h3>
          <p className="text-yellow-700">{currentTimer.label}</p>
          <TimerDisplay timer={currentTimer} />
        </div>
      )}

      {/* Controls */}
      <div className="space-y-2">
        {!sessionId ? (
          <button
            onClick={handleStartRecipe}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Start Recipe Session
          </button>
        ) : (
          <button
            onClick={handleSetTimer}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Set Timer (4 min)
          </button>
        )}
      </div>

      {/* Last Event */}
      {lastEvent && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-sm text-gray-700">Last Event</h4>
          <pre className="text-xs text-gray-600 mt-1 overflow-x-auto">
            {JSON.stringify(lastEvent, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

// Timer display component
const TimerDisplay = ({ timer }: { timer: Timer }) => {
  const [remaining, setRemaining] = useState(getTimerRemaining(timer));

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const newRemaining = getTimerRemaining(timer);
      setRemaining(newRemaining);
      
      if (newRemaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [timer]);

  return (
    <div className="text-center">
      <div className="text-2xl font-mono font-bold text-yellow-800">
        {formatTime(remaining)}
      </div>
      {remaining <= 0 && (
        <div className="text-red-600 font-semibold">Timer Complete!</div>
      )}
    </div>
  );
};

function getTimerRemaining(timer: Timer) {
  const elapsed = Math.floor((Date.now() / 1000) - timer.started_at);
  const remaining = Math.max(0, timer.duration - elapsed);
  return remaining;
} 