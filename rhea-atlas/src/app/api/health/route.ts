import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    frontend: 'rhea-atlas',
    env: process.env.NODE_ENV,
  });
}
