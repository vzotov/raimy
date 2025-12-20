import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL || 'https://35.207.14.249/api';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = request.nextUrl;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      return NextResponse.redirect(
        new URL(`/?error=${encodeURIComponent(error)}`, request.nextUrl.origin)
      );
    }

    if (!code || !state) {
      return NextResponse.redirect(
        new URL('/?error=missing_parameters', request.nextUrl.origin)
      );
    }

    const backendUrl = new URL(`${BACKEND_API_URL}/auth/callback`);
    backendUrl.searchParams.set('code', code);
    backendUrl.searchParams.set('state', state);

    const headers = new Headers();
    headers.set('origin', request.nextUrl.origin);

    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      headers.set('cookie', cookieHeader);
    }

    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers,
      redirect: 'manual', // CRITICAL: Intercept redirect and X-Auth-Token header
    });

    if (response.status === 302 || response.status === 307) {
      const location = response.headers.get('location');
      const token = response.headers.get('X-Auth-Token');

      if (!location || !token) {
        return NextResponse.json({
          error: 'Invalid response from auth service'
        }, { status: 500 });
      }

      const redirectResponse = NextResponse.redirect(location);

      // Set cookie with JWT token from backend
      // Don't set domain - let browser handle it automatically for same-site cookies
      redirectResponse.cookies.set('access_token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',  // Same-site cookie since Next.js and API are both on Vercel
        path: '/',
        maxAge: 24 * 3600  // 24 hours
      });

      return redirectResponse;
    }

    return NextResponse.redirect(
      new URL('/?error=auth_failed', request.nextUrl.origin)
    );
  } catch (error) {
    return NextResponse.redirect(
      new URL('/?error=server_error', request.nextUrl.origin)
    );
  }
}
