'use client';

import classNames from 'classnames';
import ChevronRightIcon from '@/components/icons/ChevronRightIcon';

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
      className="flex cursor-pointer items-center justify-between rounded-lg px-4 py-2 text-base font-medium text-text transition-colors duration-150 hover:bg-accent/30 hover:text-primary"
      onClick={onToggle}
    >
      <span>{title}</span>
      <ChevronRightIcon
        className={classNames('h-4 w-4 transition-transform duration-200', {
          'rotate-90': isExpanded,
        })}
      />
    </div>
  );
}
