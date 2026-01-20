'use client';
import { ThemeProvider } from '@/providers/ThemeProvider';
import { AuthProvider } from './AuthProvider';
import { ConfigProvider } from './ConfigProvider';

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ConfigProvider>{children}</ConfigProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
