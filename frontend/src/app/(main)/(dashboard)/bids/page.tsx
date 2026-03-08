/**
 * 공고 목록 페이지
 * GET /bids
 */
'use client';

import { useCallback, useEffect } from 'react';
import Link from 'next/link';
import { useBidStore } from '@/lib/stores/bid-store';
import { BidFilterBar } from '@/components/bids/BidFilterBar';
import { BidCard } from '@/components/bids/BidCard';
import { BidStatusBadge } from '@/components/bids/BidStatusBadge';
import { DeadlineBadge } from '@/components/bids/DeadlineBadge';
import { MatchScoreBadge } from '@/components/bids/MatchScoreBadge';
import type { BidItem } from '@/types/bid';

function formatBudget(budget?: number): string {
  if (!budget) return '-';
  if (budget >= 100_000_000) return `${(budget / 100_000_000).toFixed(0)}억원`;
  if (budget >= 10_000) return `${(budget / 10_000).toFixed(0)}만원`;
  return `${budget.toLocaleString()}원`;
}

function formatDeadline(deadline: string): string {
  const date = new Date(deadline);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

// 스켈레톤 로딩 행
function BidTableSkeleton() {
  return (
    <>
      {Array.from({ length: 8 }).map((_, i) => (
        <tr key={i} className="border-b border-neutral-100">
          {Array.from({ length: 6 }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <div className="h-4 bg-neutral-200 rounded animate-pulse" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// 빈 상태
function BidEmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <svg className="w-12 h-12 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p className="text-sm font-semibold text-neutral-700 mb-1">검색 조건에 맞는 공고가 없습니다</p>
      <p className="text-xs text-neutral-400 mb-4">필터를 초기화하거나 다른 검색어로 시도해보세요</p>
      <button
        onClick={onReset}
        className="px-4 py-2 text-sm font-medium border border-neutral-200 rounded-md text-neutral-600 hover:bg-neutral-50 transition-colors"
      >
        필터 초기화
      </button>
    </div>
  );
}

// 테이블 행
function BidTableRow({ bid }: { bid: BidItem }) {
  return (
    <tr className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors cursor-pointer">
      <td className="px-4 py-3">
        <span className="text-xs text-neutral-400 font-mono">{bid.bidNumber}</span>
      </td>
      <td className="px-4 py-3">
        <Link href={`/bids/${bid.id}`} className="text-sm font-medium text-neutral-800 hover:text-[#486581] line-clamp-1">
          {bid.title}
        </Link>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm text-neutral-600">{bid.organization}</span>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm text-neutral-500">{bid.category ?? '-'}</span>
      </td>
      <td className="px-4 py-3 text-right">
        <span className="text-sm font-medium text-neutral-700">{formatBudget(bid.budget)}</span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1.5">
          <BidStatusBadge status={bid.status} />
          <DeadlineBadge deadline={bid.deadline} />
        </div>
        <div className="text-xs text-neutral-400 mt-0.5">{formatDeadline(bid.deadline)}</div>
      </td>
    </tr>
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

export default function BidsPage() {
  const {
    bids,
    isLoading,
    error,
    pagination,
    filters,
    currentPage,
    fetchBids,
    setFilter,
    resetFilters,
    setPage,
  } = useBidStore();

  // 초기 로드 및 필터/페이지 변경 시 재조회
  useEffect(() => {
    fetchBids(currentPage);
  }, [fetchBids, currentPage, filters]);

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

  return (
    <div className="p-6 max-w-screen-lg mx-auto">
      {/* 페이지 헤더 */}
      <div className="mb-5">
        <h1 className="text-xl font-bold text-neutral-800">공고 목록</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          수집된 공공 입찰 공고를 확인하세요
        </p>
      </div>

      {/* 필터 바 */}
      <div className="mb-4">
        <BidFilterBar
          keyword={filters.keyword}
          status={filters.status}
          category={filters.category}
          sortBy={filters.sortBy}
          sortOrder={filters.sortOrder}
          onKeywordChange={(v) => setFilter('keyword', v)}
          onStatusChange={(v) => setFilter('status', v)}
          onCategoryChange={(v) => setFilter('category', v)}
          onSortChange={(sortBy, sortOrder) => {
            setFilter('sortBy', sortBy as typeof filters.sortBy);
            setFilter('sortOrder', sortOrder as 'asc' | 'desc');
          }}
          onReset={handleReset}
          totalCount={pagination.total}
        />
      </div>

      {/* 에러 상태 */}
      {error && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#FFEBEE] border border-[#FFCDD2] rounded-lg text-sm text-[#C62828]">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
          <button
            onClick={() => fetchBids(currentPage)}
            className="ml-auto text-xs underline hover:no-underline"
          >
            다시 시도
          </button>
        </div>
      )}

      {/* 데스크톱 테이블 뷰 */}
      <div className="hidden md:block bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 w-36">공고번호</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500">공고명</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 w-40">발주기관</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 w-24">분류</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 w-28">예산</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 w-40">상태/마감일</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <BidTableSkeleton />
            ) : bids.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <BidEmptyState onReset={handleReset} />
                </td>
              </tr>
            ) : (
              bids.map((bid) => <BidTableRow key={bid.id} bid={bid} />)
            )}
          </tbody>
        </table>
      </div>

      {/* 모바일 카드 뷰 */}
      <div className="md:hidden space-y-3">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white border border-neutral-200 rounded-lg p-4 animate-pulse">
              <div className="flex gap-2 mb-3">
                <div className="h-5 w-16 bg-neutral-200 rounded-full" />
                <div className="h-5 w-12 bg-neutral-200 rounded" />
              </div>
              <div className="h-4 w-4/5 bg-neutral-200 rounded mb-2" />
              <div className="h-3 w-3/5 bg-neutral-200 rounded" />
            </div>
          ))
        ) : bids.length === 0 ? (
          <BidEmptyState onReset={handleReset} />
        ) : (
          bids.map((bid) => <BidCard key={bid.id} bid={bid} />)
        )}
      </div>

      {/* 페이지네이션 */}
      {!isLoading && bids.length > 0 && (
        <Pagination
          page={currentPage}
          totalPages={pagination.totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
