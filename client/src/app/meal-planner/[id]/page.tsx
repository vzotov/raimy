import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import { getServerAuth } from '@/lib/serverAuth';
import MealPlannerContent from '@/components/pages/meal-planner/MealPlannerContent';
import ServerAuthGuard from '@/components/shared/ServerAuthGuard';

interface MealPlannerSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function MealPlannerSessionPage({
  params,
}: MealPlannerSessionPageProps) {
  const { id } = await params;
  const { user } = await getServerAuth();

  if (!user) {
    return null; // ServerAuthGuard will redirect
  }

  // Verify the session exists
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

    return (
      <ServerAuthGuard>
        <MealPlannerContent
          sessionId={session.id}
          sessionName={session.session_name}
          initialMessages={session.messages || []}
        />
      </ServerAuthGuard>
    );
  } catch (error) {
    console.error('Error fetching session:', error);
    notFound();
  }
}
