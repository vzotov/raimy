'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { KitchenStepContent } from '@/types/chat-message-types';

interface CookingStepProps {
  step: KitchenStepContent;
  stepIndex: number;
  totalSteps: number;
  onNext: () => void;
  onPrev: () => void;
  hasPrev: boolean;
  isLoading: boolean;
}

/**
 * Render text with **bold** markdown inline.
 */
function BoldText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i}>{part.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

function Timer({ minutes, label }: { minutes: number; label?: string }) {
  const totalSeconds = minutes * 60;
  const [remaining, setRemaining] = useState<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const start = useCallback(() => {
    setRemaining(totalSeconds);
  }, [totalSeconds]);

  useEffect(() => {
    if (remaining === null) return;

    if (remaining <= 0) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    intervalRef.current = setInterval(() => {
      setRemaining((r) => (r !== null ? r - 1 : null));
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [remaining]);

  const reset = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setRemaining(null);
  }, []);

  if (remaining === null) {
    return (
      <button
        onClick={start}
        className="mt-4 flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
      >
        <span>⏱</span>
        <span>Set {minutes}-min timer {label ? `— ${label}` : ''}</span>
      </button>
    );
  }

  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const isDone = remaining === 0;

  return (
    <div className="mt-4 flex items-center gap-3 rounded-lg border border-accent/20 bg-surface px-4 py-3">
      <span className="text-2xl font-mono font-bold text-text">
        {isDone ? 'Done!' : `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`}
      </span>
      {label && <span className="text-sm text-text/60">{label}</span>}
      <button
        onClick={reset}
        className="ml-auto text-xs text-text/40 underline hover:text-text/60"
      >
        Reset
      </button>
    </div>
  );
}

export default function CookingStep({
  step,
  stepIndex,
  totalSteps,
  onNext,
  onPrev,
  hasPrev,
  isLoading,
}: CookingStepProps) {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Step image */}
      {step.image_url && (
        <div className="w-full shrink-0 overflow-hidden" style={{ maxHeight: '40vh' }}>
          <img
            src={step.image_url}
            alt={`Step ${stepIndex + 1}`}
            className="h-full w-full object-cover"
            style={{ maxHeight: '40vh' }}
          />
        </div>
      )}

      {/* Content */}
      <div className="flex flex-1 flex-col overflow-y-auto p-5">
        {/* Step counter */}
        <div className="mb-1 text-xs font-medium uppercase tracking-wider text-text/40">
          Step {stepIndex + 1} of {totalSteps}
        </div>

        {/* Progress dots */}
        <div className="mb-5 flex gap-1.5">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i <= stepIndex ? 'bg-primary' : 'bg-accent/20'
              }`}
            />
          ))}
        </div>

        {/* Instruction */}
        <p className="flex-1 text-base leading-relaxed text-text sm:text-lg">
          <BoldText text={step.message} />
        </p>

        {/* Timer */}
        {step.timer_minutes && (
          <Timer minutes={step.timer_minutes} label={step.timer_label} />
        )}
      </div>

      {/* Navigation */}
      <div className="flex shrink-0 gap-3 border-t border-accent/20 p-4">
        <button
          onClick={onPrev}
          disabled={!hasPrev || isLoading}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-accent/20 py-3.5 text-sm font-medium text-text/70 transition-colors hover:bg-accent/10 disabled:opacity-40"
        >
          ← Previous
        </button>
        <button
          onClick={onNext}
          disabled={isLoading}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary py-3.5 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-60"
        >
          {isLoading ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            step.next_step_prompt || 'Next Step →'
          )}
        </button>
      </div>
    </div>
  );
}
