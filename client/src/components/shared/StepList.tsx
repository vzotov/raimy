import ClockIcon from '@/components/icons/ClockIcon';
import type { RecipeStep } from '@/types/recipe';

interface StepListProps {
  steps: RecipeStep[];
}

export default function StepList({ steps }: StepListProps) {
  if (steps.length === 0) return null;

  return (
    <ol className="space-y-4">
      {steps.map((step, index) => (
        <li key={step.instruction} className="flex gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary text-sm font-medium rounded-full flex items-center justify-center">
            {index + 1}
          </span>
          <div className="flex-1">
            <p className="text-text/80 leading-relaxed">{step.instruction}</p>
            {step.duration && (
              <p className="text-text/60 text-sm mt-1 flex items-center gap-1">
                <ClockIcon className="inline-block w-4 h-4" /> {step.duration}{' '}
                min
              </p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
