import MyRecipesContent from '@/components/MyRecipesContent';
import AuthPageGuard from '@/components/AuthPageGuard';

export default async function MyRecipesPage() {
  // Get user session
  const userId = '';

  return (
    <AuthPageGuard>
      <MyRecipesContent />
    </AuthPageGuard>
  );
} 