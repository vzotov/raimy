import KitchenContent from '@/components/pages/kitchen/KitchenContent';
import ServerAuthGuard from '@/components/shared/ServerAuthGuard';

export default async function KitchenPage() {
  return (
    <ServerAuthGuard>
      <KitchenContent />
    </ServerAuthGuard>
  );
}
