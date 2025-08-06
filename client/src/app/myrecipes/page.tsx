import MyRecipesContent from '@/components/pages/recipes/MyRecipesContent';
import ServerAuthGuard from '@/components/shared/ServerAuthGuard';

export default async function MyRecipesPage() {
  return (
    <ServerAuthGuard>
      <MyRecipesContent />
    </ServerAuthGuard>
  );
} 