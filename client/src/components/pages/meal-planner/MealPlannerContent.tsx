import { createToken } from '@/lib/livekit';
import MealPlannerLiveKitWrapper from './MealPlannerLiveKitWrapper';
import { getServerAuth } from '@/lib/serverAuth';
import { SessionMessage } from '@/types/meal-planner-session';

interface MealPlannerContentProps {
  sessionId: string;
  sessionName: string;
  roomName: string;
  initialMessages?: SessionMessage[];
}

export default async function MealPlannerContent({
  sessionId,
  sessionName,
  roomName,
  initialMessages = [],
}: MealPlannerContentProps) {
  const { user } = await getServerAuth();
  const userId = user?.email || '';

  // Use the session's room name for persistent LiveKit rooms
  const token = await createToken(userId, roomName);
  const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || '';

  return (
    <MealPlannerLiveKitWrapper
      serverUrl={serverUrl}
      token={token}
      sessionId={sessionId}
      sessionName={sessionName}
      initialMessages={initialMessages}
    />
  );
}
