import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import UnifiedChat from './UnifiedChat';

interface UnifiedContentProps {
  id: string;
  initialInput?: string;
}

export default async function UnifiedContent({ id, initialInput }: UnifiedContentProps) {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  try {
    const response = await fetch(`${apiUrl}/api/chat-sessions/${id}`, {
      headers: { Cookie: cookieStore.toString() },
    });

    if (!response.ok) {
      notFound();
    }

    const data = await response.json();
    const session = data.session;

    const initialRecipe = session.recipe
      ? { ...session.recipe, id: session.recipe_id || '' }
      : null;

    return (
      <UnifiedChat
        sessionId={session.id}
        sessionName={session.session_name}
        initialMessages={session.messages || []}
        initialFinished={session.finished || false}
        initialRecipe={initialRecipe}
        initialIsChanged={session.recipe_changed ?? false}
        initialInput={initialInput}
      />
    );
  } catch {
    notFound();
  }
}
