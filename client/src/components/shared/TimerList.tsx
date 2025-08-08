import React, { useState, useEffect } from 'react';

interface Timer {
  duration: number;
  label: string;
  started_at: number;
}

interface TimerListProps {
  timers: Timer[];
}

export default function TimerList({ timers }: TimerListProps) {
  const [currentTime, setCurrentTime] = useState(Date.now());

  // Update current time every second
  useEffect(() => {
    if (timers.length === 0) return;

    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);

    return () => clearInterval(interval);
  }, [timers.length]);

  if (timers.length === 0) return null;

  return (
    <div className="space-y-2">
      {timers.map((timer, index) => {
        // Calculate remaining time using currentTime state
        const elapsed = Math.floor((currentTime - timer.started_at) / 1000);
        const remaining = Math.max(0, timer.duration - elapsed);
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;

        return (
          <div
            key={index}
            className="flex flex-col"
          >
            <div className="text-2xl font-bold text-primary text-center">
              {minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}
            </div>
            <div className="text-center">
              <p className="font-medium">{timer.label}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
} 