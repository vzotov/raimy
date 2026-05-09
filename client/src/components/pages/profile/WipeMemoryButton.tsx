'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ConfirmDialog from '@/components/shared/ConfirmDialog';

export default function WipeMemoryButton() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const handleWipe = async () => {
    await fetch('/api/user/memory', {
      method: 'DELETE',
      credentials: 'include',
    });
    router.refresh();
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-sm text-danger hover:text-danger-hover transition-colors cursor-pointer"
      >
        Wipe memory
      </button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Wipe memory"
        description="This will erase everything Raimy knows about you. This action cannot be undone."
        confirmLabel="Wipe"
        variant="destructive"
        onConfirm={handleWipe}
      >
        <img
          src="/total-recall.webp"
          alt="Total Recall"
          className="w-full rounded-lg object-cover"
        />
      </ConfirmDialog>
    </>
  );
}
