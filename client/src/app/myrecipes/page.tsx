import MyRecipesContent from '@/components/pages/recipes/MyRecipesContent';
import AuthPageGuard from '@/components/shared/AuthPageGuard';

export default async function MyRecipesPage() {
  return (
    <AuthPageGuard>
      <MyRecipesContent />
    </AuthPageGuard>
  );
} 