import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import { Suspense } from 'react';
import KitchenChatSkeleton from '@/components/pages/kitchen/KitchenChatSkeleton';
import KitchenContent from '@/components/pages/kitchen/KitchenContent';

interface KitchenSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export async function generateMetadata({
  params,
}: KitchenSessionPageProps): Promise<Metadata> {
  const { id } = await params;
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const res = await fetch(`${apiUrl}/api/chat-sessions/${id}`, {
      headers: { Cookie: cookieStore.toString() },
    });

    if (!res.ok) {
      return { title: 'Kitchen' };
    }

    const data = await res.json();
    return { title: data.session?.session_name || 'Kitchen' };
  } catch {
    return { title: 'Kitchen' };
  }
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
