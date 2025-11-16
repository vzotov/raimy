import MealPlanner from './MealPlanner';
import { SessionMessage } from '@/types/meal-planner-session';

interface MealPlannerContentProps {
  sessionId: string;
  sessionName: string;
  initialMessages?: SessionMessage[];
}

export default async function MealPlannerContent({
  sessionId,
  sessionName,
  initialMessages = [],
}: MealPlannerContentProps) {
  return (
    <MealPlanner
      sessionId={sessionId}
      sessionName={sessionName}
      initialMessages={initialMessages}
    />
  );
}
