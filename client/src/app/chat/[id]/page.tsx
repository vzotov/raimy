import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import { Suspense } from 'react';
import UnifiedContent from '@/components/pages/chat/UnifiedContent';

interface ChatSessionPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ q?: string }>;
}

export async function generateMetadata({ params }: ChatSessionPageProps): Promise<Metadata> {
  const { id } = await params;
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const res = await fetch(`${apiUrl}/api/chat-sessions/${id}`, {
      headers: { Cookie: cookieStore.toString() },
    });
    if (!res.ok) return { title: 'Chat' };
    const data = await res.json();
    return { title: data.session?.session_name || 'Chat' };
  } catch {
    return { title: 'Chat' };
  }
}

function ChatSkeleton() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );
}

export default async function ChatSessionPage({ params, searchParams }: ChatSessionPageProps) {
  const { id } = await params;
  const { q } = await searchParams;

  return (
    <Suspense fallback={<ChatSkeleton />}>
      <UnifiedContent id={id} initialInput={q} />
    </Suspense>
  );
}
