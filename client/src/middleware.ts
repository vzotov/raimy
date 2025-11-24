import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  try {
    // Check authentication by calling the backend
    const response = await fetch(`${apiUrl}/auth/me`, {
      headers: {
        Cookie: request.headers.get('cookie') || '',
      },
    });

    if (!response.ok) {
      // Not authenticated, redirect to home
      return NextResponse.redirect(new URL('/', request.url));
    }

    const data = await response.json();

    if (!data.authenticated) {
      // Not authenticated, redirect to home
      return NextResponse.redirect(new URL('/', request.url));
    }

    // User is authenticated, allow request to proceed
    return NextResponse.next();
  } catch (error) {
    console.error('Middleware auth error:', error);
    // On error, redirect to home for safety
    return NextResponse.redirect(new URL('/', request.url));
  }
}

// Specify which routes should be protected
export const config = {
  matcher: [
    '/kitchen/:path*',
    '/meal-planner/:path*',
    '/myrecipes/:path*',
  ],
};