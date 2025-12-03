'use client';

interface SectionHeaderProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
}

export default function SectionHeader({
  title,
  isExpanded,
  onToggle,
}: SectionHeaderProps) {
  return (
    <div
      className="flex items-center justify-between px-4 py-2 text-base font-medium text-text hover:text-primary hover:bg-accent/30 rounded-lg transition-colors duration-150 cursor-pointer"
      onClick={onToggle}
    >
      <span>{title}</span>
      <span
        className="text-xs transition-transform duration-200"
        style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
      >
        ▶
      </span>
    </div>
  );
}