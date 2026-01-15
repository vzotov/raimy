import { Suspense } from 'react';
import RecipeCreatorContent from '@/components/pages/recipe-creator/RecipeCreatorContent';
import KitchenChatSkeleton from '@/components/pages/kitchen/KitchenChatSkeleton';

interface RecipeCreatorSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function RecipeCreatorSessionPage({
  params,
}: RecipeCreatorSessionPageProps) {
  const { id } = await params;

  return (
    <Suspense fallback={<KitchenChatSkeleton />}>
      <RecipeCreatorContent id={id} />
    </Suspense>
  );
}
