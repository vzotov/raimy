import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import RecipeCreatorChat from '@/components/pages/recipe-creator/RecipeCreatorChat';

interface RecipeCreatorContentProps {
  id: string;
}

export default async function RecipeCreatorContent({
  id,
}: RecipeCreatorContentProps) {
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

    // Transform recipe to include id from session.recipe_id
    const recipeWithId = session.recipe
      ? {
          ...session.recipe,
          id: session.recipe_id || null,
        }
      : null;

    return (
      <RecipeCreatorChat
        sessionId={session.id}
        sessionName={session.session_name}
        initialMessages={session.messages || []}
        initialRecipe={recipeWithId}
      />
    );
  } catch (error) {
    console.error('Error fetching session:', error);
    notFound();
  }
}
