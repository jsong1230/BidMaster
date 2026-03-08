/**
 * 매칭 공고 목록 페이지
 * GET /bids/matched
 */
'use client';

import { useCallback, useEffect } from 'react';
import Link from 'next/link';
import { useMatchedBidStore } from '@/lib/stores/matched-bid-store';
import { BidStatusBadge } from '@/components/bids/BidStatusBadge';
import { DeadlineBadge } from '@/components/bids/DeadlineBadge';
import { MatchScoreBadge } from '@/components/bids/MatchScoreBadge';
import { RecommendationBadge } from '@/components/bids/RecommendationBadge';
import type { MatchedBidItem, RecommendationType } from '@/types/bid-match';

function formatBudget(budget?: number): string {
  if (!budget) return '-';
  if (budget >= 100_000_000) return `${(budget / 100_000_000).toFixed(0)}억원`;
  if (budget >= 10_000) return `${(budget / 10_000).toFixed(0)}만원`;
  return `${budget.toLocaleString()}원`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

const RECOMMENDATION_TABS: { value: 'all' | RecommendationType; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'recommended', label: '추천' },
  { value: 'neutral', label: '보통' },
  { value: 'not_recommended', label: '비추천' },
];

// 회사 미등록 배너
function CompanyProfileMissingBanner() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <svg className="w-16 h-16 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <p className="text-base font-semibold text-neutral-700 mb-2">매칭 공고를 보려면 회사 프로필이 필요합니다</p>
      <p className="text-sm text-neutral-500 leading-relaxed mb-6">
        회사 프로필을 등록하면 공고와의 매칭 점수를<br />자동으로 분석하여 맞춤 공고를 제공합니다.
      </p>
      <Link
        href="/settings/company"
        className="px-6 py-2.5 text-sm font-semibold bg-[#486581] text-white rounded-md hover:bg-[#334E68] transition-colors"
      >
        회사 프로필 등록하기
      </Link>
    </div>
  );
}

// 로딩 스켈레톤
function MatchedBidSkeletonList() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white border border-neutral-200 rounded-lg p-5 animate-pulse">
          <div className="flex gap-2 mb-3">
            <div className="h-6 w-16 bg-neutral-200 rounded-full" />
            <div className="h-6 w-12 bg-neutral-200 rounded-full" />
          </div>
          <div className="h-5 w-4/5 bg-neutral-200 rounded mb-2" />
          <div className="h-4 w-3/5 bg-neutral-200 rounded mb-1" />
          <div className="h-3 w-2/3 bg-neutral-200 rounded" />
        </div>
      ))}
    </div>
  );
}

// 빈 상태
function MatchedBidEmptyState({ hasFilter, onReset }: { hasFilter: boolean; onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <svg className="w-12 h-12 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
      {hasFilter ? (
        <>
          <p className="text-sm font-semibold text-neutral-700 mb-1">해당 조건의 매칭 공고가 없습니다</p>
          <button
            onClick={onReset}
            className="mt-3 text-sm text-[#486581] hover:underline"
          >
            필터 초기화
          </button>
        </>
      ) : (
        <>
          <p className="text-sm font-semibold text-neutral-700 mb-1">아직 매칭된 공고가 없습니다</p>
          <p className="text-xs text-neutral-400">공고 수집 후 자동으로 매칭 분석이 진행됩니다.</p>
        </>
      )}
    </div>
  );
}

// 매칭 공고 카드
function MatchedBidCard({ match }: { match: MatchedBidItem }) {
  return (
    <Link href={`/bids/${match.bid.id}`}>
      <div className="bg-white border border-neutral-200 rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer h-full">
        {/* 점수 + 추천 등급 + 상태 배지 */}
        <div className="flex items-center flex-wrap gap-2 mb-3">
          <MatchScoreBadge score={match.totalScore} size="md" />
          <RecommendationBadge recommendation={match.recommendation} />
          <BidStatusBadge status={match.bid.status} />
          <DeadlineBadge deadline={match.bid.deadline} />
        </div>

        {/* 공고명 */}
        <h3 className="text-sm font-semibold text-neutral-800 mb-2 line-clamp-2 leading-snug">
          {match.bid.title}
        </h3>

        {/* 메타 정보 */}
        <div className="space-y-1 text-xs text-neutral-500 mb-3">
          <div>
            <span className="text-neutral-400">발주기관 </span>
            <span className="font-medium text-neutral-700">{match.bid.organization}</span>
          </div>
          <div className="flex items-center justify-between">
            {match.bid.budget && (
              <span>
                <span className="text-neutral-400">예산 </span>
                <span className="font-medium">{formatBudget(match.bid.budget)}</span>
              </span>
            )}
            <span>
              <span className="text-neutral-400">마감 </span>
              <span>{formatDate(match.bid.deadline)}</span>
            </span>
          </div>
        </div>

        {/* 추천 사유 한 줄 요약 */}
        {match.recommendationReason && (
          <p className="text-xs text-neutral-400 line-clamp-2 leading-relaxed border-t border-neutral-100 pt-3">
            {match.recommendationReason}
          </p>
        )}
      </div>
    </Link>
  );
}

// 페이지네이션
function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex items-center justify-center gap-1 py-4">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md disabled:opacity-40 hover:bg-neutral-50 transition-colors"
      >
        이전
      </button>
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`w-9 h-9 text-sm rounded-md transition-colors ${
            p === page
              ? 'bg-[#486581] text-white font-semibold'
              : 'border border-neutral-200 text-neutral-600 hover:bg-neutral-50'
          }`}
        >
          {p}
        </button>
      ))}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md disabled:opacity-40 hover:bg-neutral-50 transition-colors"
      >
        다음
      </button>
    </div>
  );
}

export default function MatchedBidsPage() {
  const {
    matches,
    isLoading,
    error,
    hasCompanyProfile,
    pagination,
    filters,
    currentPage,
    fetchMatchedBids,
    setFilter,
    resetFilters,
    setPage,
  } = useMatchedBidStore();

  useEffect(() => {
    fetchMatchedBids(currentPage);
  }, [fetchMatchedBids, currentPage, filters]);

  const handlePageChange = useCallback(
    (page: number) => {
      setPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    [setPage]
  );

  const handleReset = useCallback(() => {
    resetFilters();
  }, [resetFilters]);

  const hasFilter =
    filters.recommendation !== 'all' || filters.minScore > 0;

  return (
    <div className="p-6 max-w-screen-lg mx-auto">
      {/* 페이지 헤더 */}
      <div className="mb-5">
        <h1 className="text-xl font-bold text-neutral-800">매칭 공고</h1>
        {hasCompanyProfile && (
          <p className="text-sm text-neutral-500 mt-0.5">
            총 <span className="font-semibold text-neutral-700">{pagination.total.toLocaleString()}</span>건 | 내 회사와 매칭된 공고
          </p>
        )}
      </div>

      {/* 회사 프로필 미등록 */}
      {!hasCompanyProfile ? (
        <CompanyProfileMissingBanner />
      ) : (
        <>
          {/* 필터 바 */}
          <div className="bg-white border border-neutral-200 rounded-lg p-4 mb-4 flex flex-wrap items-center gap-3">
            {/* 추천 등급 탭 */}
            <div className="flex items-center gap-1">
              {RECOMMENDATION_TABS.map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setFilter('recommendation', tab.value)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    filters.recommendation === tab.value
                      ? 'bg-[#486581] text-white font-semibold'
                      : 'bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* 최소 점수 */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-neutral-500">최소 점수</label>
              <input
                type="number"
                min={0}
                max={100}
                step={5}
                value={filters.minScore}
                onChange={(e) => setFilter('minScore', Number(e.target.value))}
                className="w-20 px-2 py-1.5 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-300"
              />
            </div>

            {/* 정렬 */}
            <select
              value={`${filters.sortBy}:${filters.sortOrder}`}
              onChange={(e) => {
                const [sortBy, sortOrder] = e.target.value.split(':');
                setFilter('sortBy', sortBy as typeof filters.sortBy);
                setFilter('sortOrder', sortOrder as 'asc' | 'desc');
              }}
              className="py-1.5 pl-3 pr-8 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-300 bg-white text-neutral-700"
            >
              <option value="totalScore:desc">점수 높은순</option>
              <option value="totalScore:asc">점수 낮은순</option>
              <option value="deadline:asc">마감일순</option>
              <option value="analyzedAt:desc">분석 최신순</option>
            </select>

            {/* 초기화 */}
            {hasFilter && (
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-neutral-500 hover:text-neutral-700 border border-neutral-200 rounded-md hover:bg-neutral-50 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                초기화
              </button>
            )}
          </div>

          {/* 에러 */}
          {error && (
            <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#FFEBEE] border border-[#FFCDD2] rounded-lg text-sm text-[#C62828]">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
              <button
                onClick={() => fetchMatchedBids(currentPage)}
                className="ml-auto text-xs underline hover:no-underline"
              >
                다시 시도
              </button>
            </div>
          )}

          {/* 콘텐츠 */}
          {isLoading ? (
            <MatchedBidSkeletonList />
          ) : matches.length === 0 ? (
            <MatchedBidEmptyState hasFilter={hasFilter} onReset={handleReset} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {matches.map((match) => (
                <MatchedBidCard key={match.id} match={match} />
              ))}
            </div>
          )}

          {/* 페이지네이션 */}
          {!isLoading && matches.length > 0 && (
            <Pagination
              page={currentPage}
              totalPages={pagination.totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </>
      )}
    </div>
  );
}
