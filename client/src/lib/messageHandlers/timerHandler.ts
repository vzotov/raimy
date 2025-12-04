import type { Dispatch } from 'react';
import type { Timer } from '@/components/shared/TimerList';
import type { TimerContent } from '@/types/chat-message-types';
import type { KitchenMessageAction } from './types';

export function handleTimerMessage(
  content: TimerContent,
  dispatch: Dispatch<KitchenMessageAction>,
): void {
  if (content.duration && content.label) {
    const newTimer: Timer = {
      id: `timer-${Date.now()}`,
      duration: content.duration,
      label: content.label,
      startedAt: content.started_at || Date.now() / 1000,
    };
    dispatch({ type: 'ADD_TIMER', payload: newTimer });
  }
}
