'use client';

import Link from 'next/link';

interface CompanyOnboardingBannerProps {
  hasCompany: boolean;
}

/**
 * 대시보드 온보딩 배너
 * 회사 미등록 사용자에게 회사 프로필 등록을 안내
 */
export default function CompanyOnboardingBanner({ hasCompany }: CompanyOnboardingBannerProps) {
  if (hasCompany) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-blue-900">회사 프로필을 등록해 주세요</p>
          <p className="text-xs text-blue-700 mt-0.5">
            회사 정보를 등록하면 맞춤형 입찰 공고 매칭과 제안서 자동화를 이용할 수 있습니다.
          </p>
        </div>
      </div>
      <Link
        href="/settings/company"
        className="flex-shrink-0 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 transition-colors whitespace-nowrap"
      >
        등록하기
      </Link>
    </div>
  );
}
