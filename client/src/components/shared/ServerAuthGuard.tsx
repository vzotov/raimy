import { getServerAuth } from '@/lib/serverAuth';
import { redirect } from 'next/navigation';

interface ServerAuthGuardProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export default async function ServerAuthGuard({ 
  children, 
  redirectTo = '/auth/signin' 
}: ServerAuthGuardProps) {
  const auth = await getServerAuth();

  if (!auth.authenticated) {
    redirect(redirectTo);
  }

  return <>{children}</>;
} 