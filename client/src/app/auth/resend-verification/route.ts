import { type NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();

    const response = await fetch(`${BACKEND_API_URL}/auth/resend-verification`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: 'Resend failed' }, { status: 500 });
  }
}
