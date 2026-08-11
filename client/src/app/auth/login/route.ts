import { type NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();

    const response = await fetch(`${BACKEND_API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    const { token, user } = data;
    const authResponse = NextResponse.json({ authenticated: true, user });

    // Same cookie options used by the Google OAuth callback route, so both
    // login methods produce an identical session cookie.
    const cookieOptions: any = {
      httpOnly: true,
      secure: true,
      sameSite: 'none',
      path: '/',
      maxAge: 24 * 3600,
    };

    if (process.env.NODE_ENV === 'production') {
      cookieOptions.domain = '.raimy.app';
    }

    authResponse.cookies.set('access_token', token, cookieOptions);

    return authResponse;
  } catch (error) {
    return NextResponse.json({ detail: 'Login failed' }, { status: 500 });
  }
}
