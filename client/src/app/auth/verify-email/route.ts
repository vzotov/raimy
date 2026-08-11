import { type NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const token = request.nextUrl.searchParams.get('token');
    if (!token) {
      return NextResponse.json({ detail: 'Missing token' }, { status: 400 });
    }

    const backendUrl = new URL(`${BACKEND_API_URL}/auth/verify-email`);
    backendUrl.searchParams.set('token', token);

    const response = await fetch(backendUrl.toString());
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    const { token: jwt, user } = data;
    const authResponse = NextResponse.json({ authenticated: true, user });

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

    authResponse.cookies.set('access_token', jwt, cookieOptions);

    return authResponse;
  } catch (error) {
    return NextResponse.json({ detail: 'Verification failed' }, { status: 500 });
  }
}
