import NewMealPlanner from '@/components/pages/meal-planner/NewMealPlanner';
import ServerAuthGuard from '@/components/shared/ServerAuthGuard';

// This page shows a simple input for the first message
// No LiveKit connection until session is created
export default async function MealPlannerPage() {
  return (
    <ServerAuthGuard>
      <NewMealPlanner />
    </ServerAuthGuard>
  );
}
