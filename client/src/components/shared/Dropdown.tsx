'use client';

import classNames from 'classnames';
import { useCallback, useEffect, useRef, useState } from 'react';

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

export default function Dropdown({
  options,
  value,
  onChange,
  label,
}: DropdownProps) {
  const [open, setOpen] = useState(false);
  const [openAbove, setOpenAbove] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const handleToggle = useCallback(() => {
    if (!open && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const estimatedMenuHeight = options.length * 40 + 8;
      const spaceBelow = window.innerHeight - rect.bottom;
      setOpenAbove(spaceBelow < estimatedMenuHeight && rect.top > estimatedMenuHeight);
    }
    setOpen((prev) => !prev);
  }, [open, options.length]);

  const selected = options.find((o) => o.value === value);

  return (
    <div ref={ref} className="relative">
      {label && (
        <span className="mb-1 block text-sm text-text/60">{label}</span>
      )}
      <button
        ref={buttonRef}
        onClick={handleToggle}
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
          className={classNames(
            'ml-auto h-4 w-4 shrink-0 text-text/40 transition-transform',
            open && 'rotate-180',
          )}
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

      {open && (
        <div
          className={classNames(
            'absolute left-0 right-0 z-50 overflow-hidden rounded-lg border border-text/20 bg-surface shadow-lg',
            openAbove ? 'bottom-full mb-1' : 'top-full mt-1',
          )}
        >
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                onChange(option.value);
                setOpen(false);
              }}
              className={classNames(
                'flex w-full items-center px-3 py-2 text-sm transition-colors',
                option.value === value
                  ? 'bg-primary/10 text-text'
                  : 'text-text/70 hover:bg-surface-hover',
              )}
            >
              {option.icon && (
                <div className="mr-3 flex h-5 w-5 items-center justify-center">
                  {option.icon}
                </div>
              )}
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
