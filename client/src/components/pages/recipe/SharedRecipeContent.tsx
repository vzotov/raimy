import { notFound } from 'next/navigation';
import SharedRecipeDetailWrapper from './SharedRecipeDetailWrapper';

interface SharedRecipeContentProps {
  token: string;
}

export default async function SharedRecipeContent({
  token,
}: SharedRecipeContentProps) {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';

  const res = await fetch(`${apiUrl}/api/recipes/shared/${token}`, {
    cache: 'no-store',
  });

  if (!res.ok) notFound();

  const { recipe } = await res.json();

  return <SharedRecipeDetailWrapper recipe={recipe} shareToken={token} />;
}
