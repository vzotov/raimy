import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import KitchenChat from '@/components/pages/kitchen/KitchenChat';

interface KitchenContentProps {
  id: string;
}

export default async function KitchenContent({ id }: KitchenContentProps) {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const response = await fetch(`${apiUrl}/api/chat-sessions/${id}`, {
      headers: {
        Cookie: cookieStore.toString(),
      },
    });

    if (!response.ok) {
      notFound();
    }

    const data = await response.json();
    const session = data.session;

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
