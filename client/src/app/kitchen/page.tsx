import { createToken } from '@/lib/livekit';
import KitchenLiveKitWrapper from '@/components/pages/kitchen/KitchenLiveKitWrapper';
import AuthPageGuard from '@/components/shared/AuthPageGuard';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export default async function KitchenPage() {
  // Get user session
  const session = await getServerSession(authOptions);
  console.log('Session:', session);
  const userId = session?.user?.id || session?.user?.email || 'anonymous';
  
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
