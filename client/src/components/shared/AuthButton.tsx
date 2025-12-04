'use client';
import classNames from 'classnames';
import { useAuth } from '@/hooks/useAuth';

export default function AuthButton() {
  const { user, loading, isAuthenticated, login, logout } = useAuth();

  if (loading) {
    return <div className="px-4 py-2 rounded text-text/60">Loading...</div>;
  }

  if (isAuthenticated && user) {
    return (
      <div className="flex flex-col items-center gap-2">
        <span className="text-sm text-text/80">Signed in as {user.email}</span>
        <button
          className={classNames(
            'px-4 py-2 rounded text-white transition',
            'bg-danger hover:bg-danger-hover',
          )}
          onClick={logout}
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button
      className={classNames(
        'px-4 py-2 rounded text-white transition',
        'bg-primary hover:bg-primary-hover',
      )}
      onClick={login}
    >
      Sign in with Google
    </button>
  );
}
