'use client';

import { useState } from 'react';
import ConfirmDialog from '@/components/shared/ConfirmDialog';
import { useAuth } from '@/hooks/useAuth';

export default function DeleteAccountButton() {
  const [open, setOpen] = useState(false);
  const { logout } = useAuth();

  const handleDelete = async () => {
    await fetch('/api/user/account', {
      method: 'DELETE',
      credentials: 'include',
    });
    await logout();
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-sm text-danger hover:text-danger-hover transition-colors cursor-pointer"
      >
        Delete profile
      </button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Delete profile"
        description="This will permanently delete your account, recipes, chat history, and everything Raimy knows about you. This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </>
  );
}
