'use client';

import classNames from 'classnames';
import { useAuth } from '@/hooks/useAuth';

export default function SignOutButton() {
  const { logout } = useAuth();

  return (
    <button
      className={classNames(
        'px-4 py-2 rounded text-white transition',
        'bg-danger hover:bg-danger-hover',
      )}
      onClick={logout}
    >
      Sign out
    </button>
  );
}
