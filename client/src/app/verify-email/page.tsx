'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import LoadingScreen from '@/components/shared/LoadingScreen';
import Logo from '@/components/shared/Logo';
import { useAuth } from '@/hooks/useAuth';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { refresh } = useAuth();
  const [status, setStatus] = useState<'verifying' | 'error'>('verifying');
  const [resent, setResent] = useState(false);

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      return;
    }

    let cancelled = false;
    fetch(`/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async (response) => {
        if (cancelled) return;
        if (!response.ok) {
          setStatus('error');
          return;
        }
        await refresh();
        router.push('/');
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (status === 'verifying') {
    return <LoadingScreen />;
  }

  const handleResend = async () => {
    const email = window.prompt('Enter your email to resend the verification link:');
    if (!email) return;
    await fetch('/auth/resend-verification', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    setResent(true);
  };

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4">
      <div className="mb-6">
        <Logo size="lg" showLink={false} />
      </div>
      <div className="text-center max-w-sm flex flex-col gap-4">
        <div className="p-3 bg-red-100 text-red-800 text-sm rounded">
          This verification link is invalid or has expired.
        </div>
        {resent ? (
          <p className="text-sm text-text/60">
            If that email has a pending signup, a new link has been sent.
          </p>
        ) : (
          <button
            onClick={handleResend}
            className="text-sm text-primary hover:underline cursor-pointer"
          >
            Resend verification email
          </button>
        )}
        <button
          onClick={() => router.push('/')}
          className="text-sm text-text/60 hover:text-text transition-colors cursor-pointer"
        >
          Back to home
        </button>
      </div>
    </div>
  );
}
