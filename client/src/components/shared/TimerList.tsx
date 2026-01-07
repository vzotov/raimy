import { useEffect, useState } from 'react';
import ScrollableArea from '@/components/shared/ScrollableArea';

export interface Timer {
  id?: string;
  duration: number;
  label: string;
  startedAt: number;
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
    <ScrollableArea
      className="flex flex-1 flex-row gap-6 start-0"
      direction="horizontal"
    >
      {timers.map((timer, index) => {
        // Calculate remaining time using currentTime state
        const elapsed = Math.floor((currentTime - timer.startedAt) / 1000);
        const remaining = Math.max(0, timer.duration - elapsed);
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;

        return (
          <div
            key={timer.id || index}
            className="flex flex-col items-center w-20 shrink-0"
          >
            <div className="text-2xl font-bold text-primary text-center">
              {minutes.toString().padStart(2, '0')}:
              {seconds.toString().padStart(2, '0')}
            </div>
            <div className="text-center">
              <p className="font-medium text-sm line-clamp-2">{timer.label}</p>
            </div>
          </div>
        );
      })}
    </ScrollableArea>
  );
}
