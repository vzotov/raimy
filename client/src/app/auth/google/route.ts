import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL || 'https://35.207.14.249/api';

export async function GET(request: NextRequest) {
  try {
    const headers = new Headers();
    headers.set('origin', request.nextUrl.origin);

    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      headers.set('cookie', cookieHeader);
    }

    const response = await fetch(`${BACKEND_API_URL}/auth/login`, {
      method: 'GET',
      headers,
      redirect: 'manual', // CRITICAL: Intercept redirect to Google
    });

    if (response.status === 302 || response.status === 307) {
      const location = response.headers.get('location');
      if (!location) {
        return NextResponse.json({ error: 'Invalid redirect from auth service' }, { status: 500 });
      }
      return NextResponse.redirect(location);
    }

    return NextResponse.json(
      { error: 'OAuth initialization failed' },
      { status: response.status }
    );
  } catch (error) {
    return NextResponse.json(
      { error: 'OAuth initialization failed' },
      { status: 500 }
    );
  }
}
