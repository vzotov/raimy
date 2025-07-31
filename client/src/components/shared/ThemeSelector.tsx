'use client';
import { useState, useEffect } from 'react';
import classNames from 'classnames';
import { MoonIcon, SunIcon, CogIcon } from '@/components/icons';

export default function ThemeSelector() {
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [mounted, setMounted] = useState(false);

  const applyTheme = (newTheme: 'light' | 'dark' | 'system') => {
    if (newTheme === 'system') {
      // Remove manual theme and use system preference
      localStorage.removeItem('theme');
      const systemIsDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (systemIsDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    } else {
      // Set manual theme
      localStorage.theme = newTheme;
      if (newTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  };

  useEffect(() => {
    setMounted(true);

    // Determine current theme state
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'dark' || storedTheme === 'light') {
      setTheme(storedTheme as 'light' | 'dark');
      applyTheme(storedTheme as 'light' | 'dark');
    } else {
      // No stored theme = system preference
      setTheme('system');
      applyTheme('system');
    }
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
    applyTheme(nextTheme);
  };

  // Don't render until mounted to avoid hydration mismatch
  if (!mounted) {
    return <div className="h-10 w-10 animate-pulse rounded-lg bg-surface/50" />;
  }

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
        {theme === 'dark' ? (
          <MoonIcon className="h-5 w-5 text-text" />
        ) : theme === 'light' ? (
          <SunIcon className="h-5 w-5 text-text" />
        ) : (
          <CogIcon className="h-5 w-5 text-text" />
        )}
      </div>
      <span className="text-sm text-text/70 capitalize">{theme}</span>
    </button>
  );
}
