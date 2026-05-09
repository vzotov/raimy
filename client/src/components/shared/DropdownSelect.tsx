'use client';

import classNames from 'classnames';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

interface DropdownOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

interface DropdownProps {
  options: DropdownOption[];
  value: string;
  onChange: (value: string) => void;
  label?: string;
}

export default function DropdownSelect({
  options,
  value,
  onChange,
  label,
}: DropdownProps) {
  const selected = options.find((o) => o.value === value);

  return (
    <DropdownMenu.Root>
      {label && (
        <span className="mb-1 block text-sm text-text/60">{label}</span>
      )}
      <DropdownMenu.Trigger asChild>
        <button
          className={classNames(
            'flex w-full items-center rounded-lg px-3 py-2 transition-all duration-200',
            'border border-text/20 bg-surface/50 hover:bg-surface',
            'hover:shadow-md active:scale-95',
          )}
        >
          {selected?.icon && (
            <div className="mr-3 flex h-5 w-5 items-center justify-center">
              {selected.icon}
            </div>
          )}
          <span className="mr-2 text-sm text-text/70">{selected?.label}</span>
          <svg
            className="ml-auto h-4 w-4 shrink-0 text-text/40 transition-transform"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          sideOffset={4}
          className="z-50 min-w-[var(--radix-dropdown-menu-trigger-width)] overflow-hidden rounded-lg border border-text/20 bg-surface shadow-lg data-[state=open]:animate-dropdown-in data-[state=closed]:animate-dropdown-out"
        >
          {options.map((option) => (
            <DropdownMenu.Item
              key={option.value}
              onSelect={() => onChange(option.value)}
              className={classNames(
                'flex w-full cursor-pointer items-center px-3 py-2 text-sm outline-none transition-colors',
                option.value === value
                  ? 'bg-primary/10 text-text'
                  : 'text-text/70 data-[highlighted]:bg-surface-hover',
              )}
            >
              {option.icon && (
                <div className="mr-3 flex h-5 w-5 items-center justify-center">
                  {option.icon}
                </div>
              )}
              {option.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
