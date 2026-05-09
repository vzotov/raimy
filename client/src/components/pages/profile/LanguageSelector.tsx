'use client';

import { useState } from 'react';
import DropdownSelect from '@/components/shared/DropdownSelect';

const LANGUAGE_OPTIONS = [
  { value: 'English',    label: 'English' },
  { value: 'Spanish',    label: 'Español' },
  { value: 'French',     label: 'Français' },
  { value: 'German',     label: 'Deutsch' },
  { value: 'Italian',    label: 'Italiano' },
  { value: 'Portuguese', label: 'Português' },
  { value: 'Russian',    label: 'Русский' },
  { value: 'Chinese',    label: '中文' },
  { value: 'Japanese',   label: '日本語' },
  { value: 'Korean',     label: '한국어' },
  { value: 'Arabic',     label: 'العربية' },
  { value: 'Hindi',      label: 'हिन्दी' },
  { value: 'Dutch',      label: 'Nederlands' },
  { value: 'Polish',     label: 'Polski' },
];

export default function LanguageSelector({ initialLanguage }: { initialLanguage: string }) {
  const [language, setLanguage] = useState(initialLanguage);

  const handleChange = async (value: string) => {
    setLanguage(value);
    await fetch('/api/user/preferences', {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: 'language', value }),
    });
  };

  return <DropdownSelect options={LANGUAGE_OPTIONS} value={language} onChange={handleChange} />;
}
