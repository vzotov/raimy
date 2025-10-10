import MealPlannerContent from '@/components/pages/meal-planner/MealPlannerContent';
import ServerAuthGuard from '@/components/shared/ServerAuthGuard';

export default async function MealPlannerPage() {
  return (
    <ServerAuthGuard>
      <MealPlannerContent />
    </ServerAuthGuard>
  );
}
