'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { CogIcon, MoonIcon, SunIcon } from '@/components/icons';
import DropdownSelect from './DropdownSelect';

const themeOptions = [
  { value: 'dark', label: 'Dark', icon: <MoonIcon className="h-5 w-5 text-text" /> },
  { value: 'light', label: 'Light', icon: <SunIcon className="h-5 w-5 text-text" /> },
  { value: 'system', label: 'System', icon: <CogIcon className="h-5 w-5 text-text" /> },
];

export default function ThemeSelector() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="h-10 w-full animate-pulse rounded-lg bg-surface/50" />;
  }

  return (
    <DropdownSelect
      options={themeOptions}
      value={theme || 'system'}
      onChange={setTheme}
    />
  );
}
