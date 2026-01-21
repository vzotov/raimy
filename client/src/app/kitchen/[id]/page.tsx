import { Suspense } from 'react';
import KitchenChatSkeleton from '@/components/pages/kitchen/KitchenChatSkeleton';
import KitchenContent from '@/components/pages/kitchen/KitchenContent';

interface KitchenSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function KitchenSessionPage({
  params,
}: KitchenSessionPageProps) {
  const { id } = await params;

  return (
    <Suspense fallback={<KitchenChatSkeleton />}>
      <KitchenContent id={id} />
    </Suspense>
  );
}
