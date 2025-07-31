'use client';
import { signIn, signOut, useSession } from 'next-auth/react';
import classNames from 'classnames';

export default function AuthButton() {
  const { data: session } = useSession();

  const handleSignIn = () => signIn('google');
  const handleSignOut = () => signOut();

  if (session) {
    return (
      <div className="flex flex-col items-center gap-2">
        <span className="text-sm text-text/80">Signed in as {session.user?.email}</span>
        <button
          className={classNames(
            'px-4 py-2 rounded text-white transition',
            'bg-danger hover:bg-danger-hover',
          )}
          onClick={handleSignOut}
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
      onClick={handleSignIn}
    >
      Sign in with Google
    </button>
  );
}
