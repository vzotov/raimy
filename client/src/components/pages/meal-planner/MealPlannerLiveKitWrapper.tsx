'use client';

import { LiveKitRoom } from '@livekit/components-react';
import MealPlanner from './MealPlanner';
import { SessionMessage } from '@/types/meal-planner-session';

export default function MealPlannerLiveKitWrapper({
  serverUrl,
  token,
  sessionId,
  sessionName,
  initialMessages = [],
}: {
  serverUrl: string;
  token: string;
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
}) {
  return (
    <LiveKitRoom
      className="flex-1 flex flex-col"
      serverUrl={serverUrl}
      token={token}
      connect={true}
    >
      <MealPlanner
        sessionId={sessionId}
        sessionName={sessionName}
        initialMessages={initialMessages}
      />
    </LiveKitRoom>
  );
}
