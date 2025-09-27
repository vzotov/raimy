import { createToken } from '@/lib/livekit';
import KitchenLiveKitWrapper from './KitchenLiveKitWrapper';
import { getServerAuth } from '@/lib/serverAuth';

export default async function KitchenContent() {
  const { user } = await getServerAuth();
  const userId = user?.email || '';

  // Generate a unique room name like playground does
  const roomName = `kitchen-${Date.now()}`;
  const token = await createToken(userId, roomName);
  const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || '';

  return (
    <KitchenLiveKitWrapper serverUrl={serverUrl} token={token} />
  );
}