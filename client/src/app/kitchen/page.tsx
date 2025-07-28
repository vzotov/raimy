import { createToken } from '@/lib/livekit';
import KitchenLiveKitWrapper from '@/components/KitchenLiveKitWrapper';
import AuthPageGuard from '@/components/AuthPageGuard';

export default async function KitchenPage() {
  // Generate a unique room name like playground does
  const roomName = `kitchen-${Date.now()}`;
  const token = await createToken('user1', roomName);
  const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || '';

  return (
    <AuthPageGuard>
      <KitchenLiveKitWrapper serverUrl={serverUrl} token={token} />
    </AuthPageGuard>
  );
} 