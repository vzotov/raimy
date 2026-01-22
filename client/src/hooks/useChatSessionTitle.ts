import { useEffect } from 'react';
import { TITLE_TEMPLATE } from '@/constants/metadata';

export function useChatSessionTitle(title: string | undefined) {
  useEffect(() => {
    if (title) {
      document.title = TITLE_TEMPLATE.replace('%s', title);
    }
  }, [title]);
}
