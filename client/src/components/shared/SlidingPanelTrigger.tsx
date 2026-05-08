import type { ReactNode } from 'react';

interface SlidingPanelTriggerProps {
  onClick: () => void;
  icon: ReactNode;
  label: string;
  indicator?: boolean;
}

export default function SlidingPanelTrigger({
  onClick,
  icon,
  label,
  indicator,
}: SlidingPanelTriggerProps) {
  return (
    <button
      onClick={onClick}
      className="fixed top-[20%] right-0 z-30 md:hidden bg-surface text-text px-3 py-6 rounded-l-lg shadow-xl hover:bg-surface/90 transition-all border border-accent/20 border-r-transparent"
      aria-label={`Show ${label}`}
    >
      <div className="flex flex-col items-center gap-1">
        <div className="relative">
          {icon}
          {indicator && (
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-orange-500 rounded-full" />
          )}
        </div>
        <span className="text-xs font-medium">{label}</span>
      </div>
    </button>
  );
}
