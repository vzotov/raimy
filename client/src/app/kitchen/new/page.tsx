'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { kitchenSessions } from '@/lib/api';

export default function NewKitchenSessionPage() {
  const router = useRouter();

  useEffect(() => {
    const createSession = async () => {
      try {
        // Create a new kitchen session
        const response = await kitchenSessions.create();

        if (response.data?.session?.id) {
          // Redirect to the new session
          router.push(`/kitchen/${response.data.session.id}`);
        } else if (response.error) {
          console.error('Failed to create kitchen session:', response.error);
        }
      } catch (err) {
        console.error('Error creating kitchen session:', err);
      }
    };

    createSession();
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-lg text-text/70">Creating new kitchen session...</div>
    </div>
  );
}
