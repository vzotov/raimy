import { type NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie');

    const response = await fetch(`${BACKEND_API_URL}/auth/me`, {
      headers: {
        cookie: cookieHeader || '',
      },
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    // Rethrow prerender interruptions - these are expected with cacheComponents
    if (error instanceof Error && 'digest' in error) {
      throw error;
    }
    console.error('Auth /me error:', error);
    return NextResponse.json(
      {
        authenticated: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
