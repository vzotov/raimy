import NewMealPlanner from '@/components/pages/meal-planner/NewMealPlanner';
import ServerAuthGuard from '@/components/shared/ServerAuthGuard';

// This page shows a simple input for the first message
export default async function MealPlannerPage() {
  return (
    <ServerAuthGuard>
      <NewMealPlanner />
    </ServerAuthGuard>
  );
}
