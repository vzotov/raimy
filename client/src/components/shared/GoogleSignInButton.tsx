'use client';
import classNames from 'classnames';
import { useAuth } from '@/hooks/useAuth';

export default function GoogleSignInButton() {
  const { login } = useAuth();

  return (
    <button
      className={classNames(
        'w-full px-4 py-2 rounded text-white transition',
        'bg-primary hover:bg-primary-hover',
      )}
      onClick={() => login()}
    >
      Sign in with Google
    </button>
  );
}
