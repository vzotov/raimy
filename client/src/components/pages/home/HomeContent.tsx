'use client';
import { useRouter } from 'next/navigation';
import AuthButton from '@/components/shared/AuthButton';
import Logo from '@/components/shared/Logo';
import LoadingScreen from '@/components/shared/LoadingScreen';
import { useAuth } from '@/hooks/useAuth';

export default function HomeContent() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const handleGoToKitchen = () => router.push('/kitchen');

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className="flex flex-col justify-between sm:justify-center flex-1 max-w-2xl mx-auto w-full">
      {/* Empty space at top */}
      <span />
      
      {/* Main content centered */}
      <div className="flex flex-col justify-center items-center px-6 mx-auto">
        <div className="text-center max-w-2xl mx-auto">
          {/* Logo */}
          <div className="mb-8 flex justify-center">
            <Logo size="lg" showLink={false} />
          </div>

          {/* Hero Headline */}
          <h1 className="text-4xl md:text-5xl font-heading font-bold text-text mb-6">
            Let&apos;s cook something delicious
          </h1>

          {/* Sub-headline */}
          <p className="text-xl text-text/80 leading-relaxed mb-8">
            Vibe cooking—made for home chefs, right in your kitchen
          </p>
        </div>
      </div>

      {/* Button at bottom */}
      <div className="flex flex-col justify-end items-center pb-8">
        {user ? (
          <button
            onClick={handleGoToKitchen}
            className="px-8 py-4 bg-primary text-white rounded-full hover:bg-primary-hover transition-colors text-lg font-medium shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95"
          >
            Go to the Kitchen
          </button>
        ) : (
          <AuthButton />
        )}
      </div>
    </div>
  );
}
