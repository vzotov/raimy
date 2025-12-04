import { cookies } from 'next/headers';
import type { AuthResponse } from '@/types/auth';

export async function getServerAuth(): Promise<AuthResponse> {
  try {
    const cookieStore = await cookies();
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const response = await fetch(`${apiUrl}/auth/me`, {
      headers: {
        Cookie: cookieStore.toString(),
      },
    });

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Server auth error:', error);
  }

  return { authenticated: false };
}
