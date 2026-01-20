'use client';

import { createContext, useContext } from 'react';
import useSWR from 'swr';
import type { AppConfig } from '@/types/config';

const defaultConfig: AppConfig = {
  instacart_enabled: false,
};

const ConfigContext = createContext<AppConfig>(defaultConfig);

const configFetcher = async (url: string): Promise<AppConfig> => {
  const response = await fetch(url, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Config request failed');
  }

  return response.json();
};

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const { data } = useSWR<AppConfig>('/api/config/features', configFetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 300000, // 5 minutes
    fallbackData: defaultConfig,
  });

  return (
    <ConfigContext.Provider value={data ?? defaultConfig}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  return useContext(ConfigContext);
}
