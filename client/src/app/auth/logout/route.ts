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

    // Delete cookie with same domain attribute used when setting it
    const cookieOptions: any = {
      path: '/',
      secure: true,
      sameSite: 'none' as const
    };

    if (process.env.NODE_ENV === 'production') {
      cookieOptions.domain = '.raimy.app';
    }

    response.cookies.set('access_token', '', {
      ...cookieOptions,
      maxAge: 0  // Expire immediately
    });

    return response;
  } catch (error) {
    // Even if backend call fails, clear cookie and redirect
    const response = NextResponse.redirect(new URL('/', request.nextUrl.origin));

    const cookieOptions: any = {
      path: '/',
      secure: true,
      sameSite: 'none' as const
    };

    if (process.env.NODE_ENV === 'production') {
      cookieOptions.domain = '.raimy.app';
    }

    response.cookies.set('access_token', '', {
      ...cookieOptions,
      maxAge: 0
    });

    return response;
  }
}
