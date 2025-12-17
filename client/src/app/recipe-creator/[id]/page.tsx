import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import RecipeCreatorChat from '@/components/pages/recipe-creator/RecipeCreatorChat';

interface RecipeCreatorSessionPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function RecipeCreatorSessionPage({
  params,
}: RecipeCreatorSessionPageProps) {
  const { id } = await params;

  // Fetch session data
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const response = await fetch(`${apiUrl}/api/chat-sessions/${id}`, {
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
      <RecipeCreatorChat
        sessionId={session.id}
        sessionName={session.session_name}
        initialMessages={session.messages || []}
        initialRecipe={session.recipe}
      />
    );
  } catch (error) {
    console.error('Error fetching session:', error);
    notFound();
  }
}
