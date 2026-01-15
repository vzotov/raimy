import { Suspense } from 'react';
import KitchenContent from '@/components/pages/kitchen/KitchenContent';
import KitchenChatSkeleton from '@/components/pages/kitchen/KitchenChatSkeleton';

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
