import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export default async function NewRecipeCreatorSessionPage() {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();

  let sessionId: string | null = null;

  try {
    const response = await fetch(`${apiUrl}/api/chat-sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: cookieStore.toString(),
      },
      body: JSON.stringify({ session_type: 'recipe-creator' }),
    });

    if (response.ok) {
      const data = await response.json();
      sessionId = data.session?.id ?? null;
    }
  } catch {
    // API error - fall through to redirect to /recipe-creator
  }

  if (sessionId) {
    redirect(`/recipe-creator/${sessionId}`);
  }

  redirect('/recipe-creator');
}
