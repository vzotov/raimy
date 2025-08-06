'use client';
import { useAuth } from '@/hooks/useAuth';
import LoadingScreen from './LoadingScreen';

interface AuthPageGuardProps {
  children: React.ReactNode;
}

export default function AuthPageGuard({ children }: AuthPageGuardProps) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-text mb-4">Authentication Required</h1>
          <p className="text-text/70 mb-6">
            Please sign in to access this page.
          </p>
          <button
            onClick={() => window.location.href = '/auth/login'}
            className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition"
          >
            Sign in with Google
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
