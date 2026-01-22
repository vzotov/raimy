import type { Metadata } from 'next';
import { TITLE_TEMPLATE } from '@/constants/metadata';

export const metadata: Metadata = {
  title: {
    template: TITLE_TEMPLATE,
    default: 'Kitchen',
  },
};

export default function KitchenLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
