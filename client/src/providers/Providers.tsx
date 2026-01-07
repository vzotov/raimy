'use client';
import { ThemeProvider } from '@/providers/ThemeProvider';
import { AuthProvider } from './AuthProvider';

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>{children}</AuthProvider>
    </ThemeProvider>
  );
}
