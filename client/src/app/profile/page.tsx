import type { Metadata } from 'next';
import { Suspense } from 'react';
import ProfileContent from '@/components/pages/profile/ProfileContent';
import ProfileContentSkeleton from '@/components/pages/profile/ProfileContentSkeleton';

export const metadata: Metadata = {
  title: 'Profile',
};

export default function ProfilePage() {
  return (
    <div className="min-h-dvh bg-background py-8 pb-24 sm:pb-8 overflow-auto">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text">Profile</h1>
        </div>

        <Suspense fallback={<ProfileContentSkeleton />}>
          <ProfileContent />
        </Suspense>
      </div>
    </div>
  );
}
