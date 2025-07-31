'use client';

import { LiveKitRoom } from '@livekit/components-react';
import Kitchen from '@/components/pages/kitchen/Kitchen';

export default function KitchenLiveKitWrapper({
  serverUrl,
  token,
}: {
  serverUrl: string;
  token: string;
}) {
  return (
    <LiveKitRoom serverUrl={serverUrl} token={token} connect={true}>
      <Kitchen />
    </LiveKitRoom>
  );
}
