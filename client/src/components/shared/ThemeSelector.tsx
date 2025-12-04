'use client';
import classNames from 'classnames';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { CogIcon, MoonIcon, SunIcon } from '@/components/icons';

export default function ThemeSelector() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleThemeToggle = () => {
    let nextTheme: 'light' | 'dark' | 'system';

    // Cycle: dark → light → system → dark
    if (theme === 'dark') {
      nextTheme = 'light';
    } else if (theme === 'light') {
      nextTheme = 'system';
    } else {
      nextTheme = 'dark';
    }

    setTheme(nextTheme);
  };

  // Don't render until mounted to avoid hydration mismatch
  if (!mounted) {
    return <div className="h-10 w-10 animate-pulse rounded-lg bg-surface/50" />;
  }

  const displayTheme = theme === 'system' ? 'system' : resolvedTheme || 'light';

  return (
    <button
      onClick={handleThemeToggle}
      className={classNames(
        'flex items-center rounded-lg px-3 py-2 transition-all duration-200',
        'border border-accent/20 bg-surface/50 hover:bg-surface',
        'hover:shadow-md active:scale-95',
      )}
      aria-label={`Current theme: ${theme}`}
    >
      <div className="mr-3 flex h-5 w-5 items-center justify-center">
        {displayTheme === 'dark' ? (
          <MoonIcon className="h-5 w-5 text-text" />
        ) : displayTheme === 'light' ? (
          <SunIcon className="h-5 w-5 text-text" />
        ) : (
          <CogIcon className="h-5 w-5 text-text" />
        )}
      </div>
      <span className="text-sm text-text/70 capitalize">{theme}</span>
    </button>
  );
}
