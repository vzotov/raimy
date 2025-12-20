import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL;

export async function GET(request: NextRequest) {
  try {
    // Call backend logout endpoint (for any cleanup/logging)
    if (BACKEND_API_URL) {
      await fetch(`${BACKEND_API_URL}/auth/logout`, {
        method: 'GET',
      }).catch(() => {
        // Ignore errors - we'll clear cookie anyway
      });
    }

    // Redirect to home and clear cookie
    const response = NextResponse.redirect(new URL('/', request.nextUrl.origin));
    response.cookies.delete('access_token');

    return response;
  } catch (error) {
    // Even if backend call fails, clear cookie and redirect
    const response = NextResponse.redirect(new URL('/', request.nextUrl.origin));
    response.cookies.delete('access_token');
    return response;
  }
}
