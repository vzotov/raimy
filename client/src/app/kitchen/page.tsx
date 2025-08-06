import { createToken } from '@/lib/livekit';
import KitchenLiveKitWrapper from '@/components/pages/kitchen/KitchenLiveKitWrapper';
import AuthPageGuard from '@/components/shared/AuthPageGuard';
import { getServerAuth } from '@/lib/serverAuth';

export default async function KitchenPage() {
  const { user } = await getServerAuth();
  const userId = user!.email;
  
  // Generate a unique room name like playground does
  const roomName = `kitchen-${Date.now()}`;
  const token = await createToken(userId, roomName);
  const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || '';

  return (
    <AuthPageGuard>
      <KitchenLiveKitWrapper serverUrl={serverUrl} token={token} />
    </AuthPageGuard>
  );
}
