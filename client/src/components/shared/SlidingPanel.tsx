'use client';

import classNames from 'classnames';
import type { ReactNode } from 'react';

interface SlidingPanelProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}

export default function SlidingPanel({
  isOpen,
  onClose,
  children,
}: SlidingPanelProps) {
  return (
    <>
      {/* Sliding panel */}
      <div
        className={classNames(
          'fixed md:sticky top-0 right-0 z-50 h-screen w-80 md:w-96 bg-surface/95 backdrop-blur-md border-l border-accent/20 flex flex-col transition-all duration-300 md:translate-x-0 shadow-xl md:shadow-none',
          { 'translate-x-0': isOpen, 'translate-x-full': !isOpen },
        )}
      >
        {children}
      </div>

      {/* Backdrop overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden transition-opacity duration-300"
          onClick={onClose}
        />
      )}
    </>
  );
}
