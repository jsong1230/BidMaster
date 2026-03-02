/**
 * 인증 미들웨어
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 보호된 경로 목록
const protectedPaths = [
  '/dashboard',
  '/bids',
  '/proposals',
  '/settings',
  '/teams',
];

// 인증 전용 경로 목록 (로그인된 사용자 접근 불가)
const authOnlyPaths = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 정적 파일 및 API 경로는 미들웨어 스킵
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/static') ||
    pathname.includes('.') // 이미지, 폰트 등
  ) {
    return;
  }

  // 토큰 확인
  const accessToken = request.cookies.get('access_token');
  const refreshToken = request.cookies.get('refresh_token');
  const isAuthenticated = !!(accessToken || refreshToken);

  // 보호된 경로 접근 시 인증 확인
  if (protectedPaths.some(path => pathname.startsWith(path))) {
    if (!isAuthenticated) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  // 인증 전용 경로 접근 시 이미 로그인된 사용자 리다이렉트
  if (authOnlyPaths.some(path => pathname.startsWith(path))) {
    if (isAuthenticated) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }
}
