'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import HourglassIcon from '@/components/icons/HourglassIcon';
import InstacartCarrotIcon from '@/components/icons/InstacartCarrotIcon';

interface InstacartButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  loadingText?: string;
}

export default function InstacartButton({
  onClick,
  disabled = false,
  loading = false,
  loadingText = 'Opening...',
}: InstacartButtonProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted && resolvedTheme === 'dark';

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        h-[46px] px-[18px] rounded-full
        text-sm font-medium transition-colors
        flex items-center justify-center gap-2
        cursor-pointer disabled:cursor-not-allowed disabled:opacity-50
        ${
          isDark
            ? 'bg-[#003D29] text-[#FAF1E5]'
            : 'bg-[#FAF1E5] text-[#003D29] border border-[#EFE9E1]'
        }
      `}
    >
      {loading ? (
        <>
          <HourglassIcon className="animate-spin w-[22px] h-[22px]" />
          {loadingText}
        </>
      ) : (
        <>
          <InstacartCarrotIcon className="w-[22px] h-[22px]" />
          Get Recipe Ingredients
        </>
      )}
    </button>
  );
}
