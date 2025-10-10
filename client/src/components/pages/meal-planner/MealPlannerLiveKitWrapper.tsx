'use client';

import { LiveKitRoom } from '@livekit/components-react';
import MealPlanner from './MealPlanner';

export default function MealPlannerLiveKitWrapper({
  serverUrl,
  token,
}: {
  serverUrl: string;
  token: string;
}) {
  return (
    <LiveKitRoom
      className="flex-1 flex flex-col"
      serverUrl={serverUrl}
      token={token}
      connect={true}
    >
      <MealPlanner />
    </LiveKitRoom>
  );
}
