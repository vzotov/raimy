import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import KitchenChat from '@/components/pages/kitchen/KitchenChat';

interface KitchenSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function KitchenSessionPage({
  params,
}: KitchenSessionPageProps) {
  const { id } = await params;

  // Fetch session data (reuses meal planner sessions endpoint)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const response = await fetch(`${apiUrl}/api/meal-planner-sessions/${id}`, {
      headers: {
        Cookie: cookieStore.toString(),
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      notFound();
    }

    const data = await response.json();
    const session = data.session;
    console.log('Fetched kitchen session:', session);

    // Verify this is a kitchen session
    if (session.session_type !== 'kitchen') {
      notFound();
    }

    return (
      <KitchenChat
        sessionId={session.id}
        sessionName={session.session_name}
        initialMessages={session.messages || []}
        initialIngredients={session.ingredients || []}
      />
    );
  } catch (error) {
    console.error('Error fetching kitchen session:', error);
    notFound();
  }
}
