'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Logo from '@/components/shared/Logo';

const inputClassName =
  'w-full text-sm bg-background border border-text/20 rounded-lg px-3 py-2 text-text/80';

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading || !token) return;

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const response = await fetch('/auth/reset-password', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Something went wrong');
        return;
      }

      setDone(true);
    } catch {
      setError('Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4">
      <div className="mb-6">
        <Logo size="lg" showLink={false} />
      </div>

      <div className="w-full max-w-sm flex flex-col gap-4">
        {!token ? (
          <div className="p-3 bg-red-100 text-red-800 text-sm rounded">
            This reset link is invalid.
          </div>
        ) : done ? (
          <>
            <div className="p-3 bg-green-100 text-green-800 text-sm rounded">
              Password updated. You can now sign in with your new password.
            </div>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 rounded text-white bg-primary hover:bg-primary-hover transition"
            >
              Back to home
            </button>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            {error && (
              <div className="p-3 bg-red-100 text-red-800 text-sm rounded">{error}</div>
            )}
            <input
              type="password"
              name="password"
              autoComplete="new-password"
              required
              minLength={8}
              placeholder="New password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClassName}
            />
            <input
              type="password"
              name="confirmPassword"
              autoComplete="new-password"
              required
              minLength={8}
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClassName}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded text-white bg-primary hover:bg-primary-hover transition disabled:opacity-50"
            >
              {loading ? 'Please wait...' : 'Reset password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
