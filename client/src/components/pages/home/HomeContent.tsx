'use client';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import AuthButton from '@/components/shared/AuthButton';

export default function HomeContent() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const handleGoToKitchen = () => router.push('/kitchen');

  if (status === 'loading') {
    return <div className="text-lg">Loading...</div>;
  }

  if (session) {
    return (
      <button
        onClick={handleGoToKitchen}
        className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-lg font-medium"
      >
        Go to Kitchen
      </button>
    );
  }

  return <AuthButton />;
}
