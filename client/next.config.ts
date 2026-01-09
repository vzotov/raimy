import type { NextConfig } from 'next';

const BACKEND_API_URL = process.env.API_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  compiler: {
    // Remove console logs in production (keep errors and warnings)
    removeConsole:
      process.env.NODE_ENV === 'production'
        ? {
            exclude: ['error', 'warn'],
          }
        : false,
  },
  async rewrites() {
    return [
      // Proxy all /api requests to backend for general API calls
      // Auth-specific routes (/auth/*) are handled by App Router routes
      {
        source: '/api/:path*',
        destination: `${BACKEND_API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
