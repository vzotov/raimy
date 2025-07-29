import MyRecipesContent from '@/components/MyRecipesContent';
import AuthPageGuard from '@/components/AuthPageGuard';

export default async function MyRecipesPage() {
  return (
    <AuthPageGuard>
      <MyRecipesContent />
    </AuthPageGuard>
  );
} 