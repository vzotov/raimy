import Logo from '@/components/shared/Logo';

export default function LoadingScreen() {
  return (
    <div className="flex-1 flex flex-col justify-center items-center">
      <div className="text-center">
        <div className="mb-4">
          <Logo size="lg" showLink={false} />
        </div>
        <div className="text-lg text-text/60">Loading...</div>
      </div>
    </div>
  );
} 