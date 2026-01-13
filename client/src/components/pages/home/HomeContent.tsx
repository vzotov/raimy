'use client';
import { useRouter } from 'next/navigation';
import ChefHatIcon from '@/components/icons/ChefHatIcon';
import NotebookIcon from '@/components/icons/NotebookIcon';
import AuthButton from '@/components/shared/AuthButton';
import LoadingScreen from '@/components/shared/LoadingScreen';
import Logo from '@/components/shared/Logo';
import { useAuth } from '@/hooks/useAuth';
import HomePageNavCard from './HomePageNavCard';

export default function HomeContent() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const handleGoToKitchen = () => router.push('/kitchen');
  const handleGoToRecipeCreator = () => router.push('/recipe-creator');

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
          <p className="text-xl text-text/80 leading-relaxed sm:mb-8">
            Vibe cooking—made for home chefs, right in your kitchen
          </p>
        </div>
      </div>

      {/* Navigation cards at bottom */}
      <div className="flex flex-col justify-end items-center pb-8 px-4">
        {user ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 w-full max-w-2xl">
            <HomePageNavCard
              icon={<NotebookIcon className="w-6 h-6 md:w-8 md:h-8" />}
              title="Recipe Creator"
              description="Create and save custom recipes based on your preferences"
              onClick={handleGoToRecipeCreator}
            />
            <HomePageNavCard
              icon={<ChefHatIcon className="w-6 h-6" />}
              title="Kitchen"
              description="Get step-by-step guidance while you cook"
              onClick={handleGoToKitchen}
            />
          </div>
        ) : (
          <AuthButton />
        )}
      </div>
    </div>
  );
}
