import ClockIcon from '@/components/icons/ClockIcon';
import HourglassIcon from '@/components/icons/HourglassIcon';
import type { RecipeStep } from '@/types/recipe';

interface StepListProps {
  steps: RecipeStep[];
  onGenerateImage?: (stepIndex: number) => void;
  generatingStepIndex?: number | null;
}

export default function StepList({
  steps,
  onGenerateImage,
  generatingStepIndex,
}: StepListProps) {
  if (steps.length === 0) return null;

  const isGenerating = generatingStepIndex !== undefined && generatingStepIndex !== null;

  return (
    <ol className="space-y-4">
      {steps.map((step, index) => (
        <li key={step.instruction} className="flex gap-3">
          <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary text-sm font-medium rounded-full flex items-center justify-center">
            {index + 1}
          </span>
          <div className="flex-1">
            {step.image_url && (
              <div className="mb-3 rounded-xl overflow-hidden">
                <img
                  src={step.image_url}
                  alt={`Step ${index + 1}`}
                  className="w-full h-auto object-cover"
                  loading="lazy"
                />
              </div>
            )}
            <p className="text-text/80 leading-relaxed">{step.instruction}</p>
            {step.duration && (
              <p className="text-text/60 text-sm mt-1 flex items-center gap-1">
                <ClockIcon className="inline-block w-4 h-4" /> {step.duration}{' '}
                min
              </p>
            )}
            {!step.image_url && onGenerateImage && (
              <button
                onClick={() => onGenerateImage(index)}
                disabled={isGenerating}
                className="mt-2 flex items-center gap-1.5 px-3 py-1.5 text-xs
                           text-text/60 hover:text-text/80 bg-accent/10 hover:bg-accent/20
                           disabled:opacity-50 disabled:cursor-not-allowed
                           rounded-lg transition-colors"
              >
                {generatingStepIndex === index ? (
                  <>
                    <HourglassIcon className="w-3.5 h-3.5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Generate image
                  </>
                )}
              </button>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
