import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Suspense } from 'react';
import './globals.css';
import GoogleAnalytics from '@/components/GoogleAnalytics';
import LayoutContent from '@/components/LayoutContent';
import { DEFAULT_TITLE, TITLE_TEMPLATE } from '@/constants/metadata';
import Providers from '@/providers/Providers';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: {
    template: TITLE_TEMPLATE,
    default: DEFAULT_TITLE,
  },
  description: 'Kitchen Assistant. Vibe cooking with AI agent.',
  keywords: [
    'cooking',
    'kitchen',
    'recipes',
    'AI',
    'artificial intelligence',
    'food',
    'assistant',
    'vibe cooking',
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${inter.variable} antialiased`}>
        <Suspense>
          <GoogleAnalytics />
          <Providers>
            <LayoutContent>{children}</LayoutContent>
          </Providers>
        </Suspense>
      </body>
    </html>
  );
}
