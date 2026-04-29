import type { Metadata } from 'next';
import { TITLE_TEMPLATE } from '@/constants/metadata';

export const metadata: Metadata = {
  title: {
    template: TITLE_TEMPLATE,
    default: 'Chat',
  },
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return children;
}
