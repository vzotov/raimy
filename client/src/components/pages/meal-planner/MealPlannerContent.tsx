import { createToken } from '@/lib/livekit';
import MealPlannerLiveKitWrapper from './MealPlannerLiveKitWrapper';
import { getServerAuth } from '@/lib/serverAuth';

export default async function MealPlannerContent() {
  const { user } = await getServerAuth();
  const userId = user?.email || '';

  // Generate room name for meal planner
  // TODO: Use conversation ID for persistent rooms
  const roomName = `meal-planner-${Date.now()}`;
  const token = await createToken(userId, roomName);
  const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || '';

  return (
    <MealPlannerLiveKitWrapper serverUrl={serverUrl} token={token} />
  );
}
