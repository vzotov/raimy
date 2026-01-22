import type { Metadata } from 'next';
import { TITLE_TEMPLATE } from '@/constants/metadata';

export const metadata: Metadata = {
  title: {
    template: TITLE_TEMPLATE,
    default: 'Recipe Creator',
  },
};

export default function RecipeCreatorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
