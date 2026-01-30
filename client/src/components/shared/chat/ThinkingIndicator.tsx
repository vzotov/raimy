import { ChefHatIcon } from '@/components/icons';

interface ThinkingIndicatorProps {
  message: string;
}

export default function ThinkingIndicator({ message }: ThinkingIndicatorProps) {
  return (
    <div className="flex items-center gap-2 py-2 px-4 mb-2">
      <ChefHatIcon className="w-5 h-5 text-primary origin-bottom animate-pendulum" />
      <span className="text-sm text-text/60">{message}</span>
    </div>
  );
}
