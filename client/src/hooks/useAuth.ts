'use client';
import useSWR from 'swr';
import type { AuthResponse } from '@/types/auth';

const authFetcher = async (url: string): Promise<AuthResponse> => {
  const response = await fetch(`${url}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Auth request failed');
  }

  return response.json();
};

export function useAuth() {
  const { data, error, isLoading, mutate } = useSWR<AuthResponse>(
    '/auth/me',
    authFetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      dedupingInterval: 60000, // 1 minute
    },
  );

  const user = data?.authenticated ? data.user : null;
  const isAuthenticated = data?.authenticated || false;

  const login = () => {
    window.location.href = `/auth/login`;
  };

  const logout = async () => {
    const response = await fetch(`/auth/logout`, {
      method: 'GET',
      credentials: 'include',
    });

    if (response.ok) {
      window.location.reload();
    } else {
      throw new Error('Logout failed');
    }
  };

  return {
    user,
    isAuthenticated,
    loading: isLoading,
    error,
    login,
    logout,
    refresh: () => mutate(),
  };
}
