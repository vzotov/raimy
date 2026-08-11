'use client';

import { useState } from 'react';
import * as AlertDialog from '@radix-ui/react-alert-dialog';

interface ForgotPasswordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function ForgotPasswordDialog({
  open,
  onOpenChange,
}: ForgotPasswordDialogProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (loading) return;
    setLoading(true);
    try {
      await fetch('/auth/forgot-password', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email }),
      });
    } finally {
      setLoading(false);
      setSent(true);
    }
  };

  const handleOpenChange = (nextOpen: boolean) => {
    onOpenChange(nextOpen);
    if (!nextOpen) {
      setEmail('');
      setSent(false);
    }
  };

  return (
    <AlertDialog.Root open={open} onOpenChange={handleOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm data-[state=open]:animate-overlay-in data-[state=closed]:animate-overlay-out" />
        <AlertDialog.Content className="fixed top-1/2 left-1/2 z-50 w-[90vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl bg-surface p-6 shadow-xl data-[state=open]:animate-dialog-in data-[state=closed]:animate-dialog-out">
          <AlertDialog.Title className="text-lg font-semibold text-text">
            Reset your password
          </AlertDialog.Title>
          <AlertDialog.Description className="mt-2 text-sm text-text/70">
            {sent
              ? 'If an account exists for that email, a reset link has been sent.'
              : "Enter your email and we'll send you a reset link."}
          </AlertDialog.Description>

          {!sent && (
            <form onSubmit={handleSubmit} className="mt-4">
              <input
                type="email"
                name="email"
                autoComplete="email"
                required
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full text-sm bg-background border border-text/20 rounded-lg px-3 py-2 text-text/80"
              />
            </form>
          )}

          <div className="mt-6 flex justify-end gap-3">
            <AlertDialog.Cancel asChild>
              <button className="rounded-lg px-4 py-2 text-sm font-medium text-text/70 hover:bg-surface-hover transition-colors cursor-pointer">
                {sent ? 'Close' : 'Cancel'}
              </button>
            </AlertDialog.Cancel>
            {!sent && (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="rounded-lg px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Send reset link'}
              </button>
            )}
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
