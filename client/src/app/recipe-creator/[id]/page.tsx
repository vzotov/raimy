import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import { Suspense } from 'react';
import KitchenChatSkeleton from '@/components/pages/kitchen/KitchenChatSkeleton';
import RecipeCreatorContent from '@/components/pages/recipe-creator/RecipeCreatorContent';

interface RecipeCreatorSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export async function generateMetadata({
  params,
}: RecipeCreatorSessionPageProps): Promise<Metadata> {
  const { id } = await params;
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const res = await fetch(`${apiUrl}/api/chat-sessions/${id}`, {
      headers: { Cookie: cookieStore.toString() },
    });

    if (!res.ok) {
      return { title: 'Recipe Creator' };
    }

    const data = await res.json();
    return { title: data.session?.session_name || 'Recipe Creator' };
  } catch {
    return { title: 'Recipe Creator' };
  }
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
