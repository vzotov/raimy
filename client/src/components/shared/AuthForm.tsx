'use client';
import { useState } from 'react';
import classNames from 'classnames';
import GoogleSignInButton from '@/components/shared/GoogleSignInButton';
import ForgotPasswordDialog from '@/components/shared/ForgotPasswordDialog';
import { useAuth } from '@/hooks/useAuth';

const inputClassName =
  'w-full text-sm bg-background border border-text/20 rounded-lg px-3 py-2 text-text/80';

export default function AuthForm() {
  const { refresh } = useAuth();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signupComplete, setSignupComplete] = useState(false);
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);

  const toggleMode = () => {
    setMode((m) => (m === 'login' ? 'signup' : 'login'));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setError(null);
    setLoading(true);

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/signup';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Something went wrong');
        return;
      }

      if (mode === 'signup') {
        setSignupComplete(true);
      } else {
        void refresh();
      }
    } catch {
      setError('Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (signupComplete) {
    return (
      <div className="w-full max-w-sm">
        <div className="p-3 bg-green-100 text-green-800 text-sm rounded">
          Check your email to verify your account before signing in.
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-sm flex flex-col gap-4">
      <GoogleSignInButton />

      <div className="flex items-center gap-3 text-text/40 text-xs">
        <div className="flex-1 h-px bg-text/20" />
        or
        <div className="flex-1 h-px bg-text/20" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {error && (
          <div className="p-3 bg-red-100 text-red-800 text-sm rounded">{error}</div>
        )}

        <input
          type="email"
          name="email"
          autoComplete="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={inputClassName}
        />
        <input
          type="password"
          name="password"
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          required
          minLength={8}
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={inputClassName}
        />

        {mode === 'login' && (
          <button
            type="button"
            onClick={() => setForgotPasswordOpen(true)}
            className="self-end text-xs text-text/60 hover:text-text transition-colors cursor-pointer"
          >
            Forgot password?
          </button>
        )}

        <button
          type="submit"
          disabled={loading}
          className={classNames(
            'px-4 py-2 rounded text-white transition',
            'bg-primary hover:bg-primary-hover disabled:opacity-50',
          )}
        >
          {loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Sign up'}
        </button>
      </form>

      <button
        type="button"
        onClick={toggleMode}
        className="text-sm text-text/60 hover:text-text transition-colors cursor-pointer"
      >
        {mode === 'login'
          ? "Don't have an account? Sign up"
          : 'Already have an account? Sign in'}
      </button>

      <ForgotPasswordDialog open={forgotPasswordOpen} onOpenChange={setForgotPasswordOpen} />
    </div>
  );
}
