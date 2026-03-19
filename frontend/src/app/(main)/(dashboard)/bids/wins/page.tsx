/**
 * 낙찰 이력 페이지
 * 요약 KPI + 필터 + 테이블 + 페이지네이션
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { dashboardApi } from '@/lib/api/dashboard';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { formatAmount, formatDate, formatWinRate } from '@/lib/utils/format';
import type { WinHistoryItem, WinHistoryParams } from '@/types/dashboard';
import type { PaginationMeta } from '@/lib/api/client';

/** 테이블 스켈레톤 */
function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 6 }).map((_, i) => (
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

/** 빈 상태 */
function EmptyState({
  hasFilter,
  onReset,
}: {
  hasFilter: boolean;
  onReset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <svg className="w-12 h-12 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
      <p className="text-sm font-semibold text-neutral-700 mb-1">
        {hasFilter ? '해당 기간에 낙찰 이력이 없습니다' : '아직 낙찰 이력이 없습니다'}
      </p>
      {hasFilter && (
        <button
          onClick={onReset}
          className="mt-3 px-4 py-2 text-sm font-medium border border-neutral-200 rounded-md text-neutral-600 hover:bg-neutral-50 transition-colors"
        >
          필터 초기화
        </button>
      )}
    </div>
  );
}

/** 페이지네이션 */
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

const defaultMeta: PaginationMeta = { page: 1, pageSize: 20, total: 0, totalPages: 0 };

export default function WinsPage() {
  const [wins, setWins] = useState<WinHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationMeta>(defaultMeta);
  const [currentPage, setCurrentPage] = useState(1);

  // 필터 상태
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortBy, setSortBy] = useState<'resultAt' | 'myBidPrice'>('resultAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const hasFilter = Boolean(startDate || endDate);

  const fetchWins = useCallback(
    async (page = 1) => {
      setIsLoading(true);
      setError(null);
      try {
        const params: WinHistoryParams = {
          page,
          pageSize: 20,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          sortBy,
          sortOrder,
        };
        const result = await dashboardApi.getWinHistory(params);
        setWins(result.items);
        setPagination(result.meta);
      } catch (err: unknown) {
        const e = err as { message?: string };
        setError(e.message ?? '낙찰 이력을 불러올 수 없습니다.');
      } finally {
        setIsLoading(false);
      }
    },
    [startDate, endDate, sortBy, sortOrder]
  );

  useEffect(() => {
    fetchWins(currentPage);
  }, [fetchWins, currentPage]);

  const handlePageChange = useCallback(
    (page: number) => {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    []
  );

  const handleReset = useCallback(() => {
    setStartDate('');
    setEndDate('');
    setSortBy('resultAt');
    setSortOrder('desc');
    setCurrentPage(1);
  }, []);

  // 요약 KPI 계산
  const totalWonAmount = wins.reduce((sum, w) => sum + (w.myBidPrice ?? 0), 0);
  const avgBidPrice =
    wins.length > 0 ? totalWonAmount / wins.length : 0;
  const avgBidRate =
    wins.filter((w) => w.bidRate != null).length > 0
      ? (wins.reduce((sum, w) => sum + (w.bidRate ?? 0), 0) /
          wins.filter((w) => w.bidRate != null).length) *
        100
      : 0;

  return (
    <div className="p-6 max-w-screen-lg mx-auto">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-neutral-800">낙찰 이력</h1>
          {!isLoading && (
            <p className="text-sm text-neutral-500 mt-0.5">
              총 <span className="font-semibold text-neutral-700">{pagination.total}건</span>
            </p>
          )}
        </div>
      </div>

      {/* 요약 KPI */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
          value={`${pagination.total}건`}
          label="총 낙찰 건수"
          iconBgClass="bg-green-50"
          iconColorClass="text-green-500"
          isLoading={isLoading}
        />
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          value={formatAmount(totalWonAmount)}
          label="총 낙찰금액"
          iconBgClass="bg-blue-50"
          iconColorClass="text-blue-500"
          isLoading={isLoading}
        />
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          }
          value={formatAmount(avgBidPrice)}
          label="평균 낙찰가"
          iconBgClass="bg-[#F0F4F8]"
          iconColorClass="text-[#627D98]"
          isLoading={isLoading}
        />
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
          value={formatWinRate(avgBidRate)}
          label="평균 낙찰률"
          iconBgClass="bg-[#ECEFF1]"
          iconColorClass="text-[#78909C]"
          isLoading={isLoading}
        />
      </div>

      {/* 필터 바 */}
      <div className="bg-white border border-neutral-200 rounded-lg p-3 mb-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-neutral-500 whitespace-nowrap">시작일</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setCurrentPage(1);
            }}
            className="px-2 py-1.5 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-1 focus:ring-[#486581]"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-neutral-500 whitespace-nowrap">종료일</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setCurrentPage(1);
            }}
            className="px-2 py-1.5 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-1 focus:ring-[#486581]"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-neutral-500 whitespace-nowrap">정렬</label>
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [by, order] = e.target.value.split('-') as [
                'resultAt' | 'myBidPrice',
                'asc' | 'desc',
              ];
              setSortBy(by);
              setSortOrder(order);
              setCurrentPage(1);
            }}
            className="px-2 py-1.5 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-1 focus:ring-[#486581]"
          >
            <option value="resultAt-desc">결과일 최신순</option>
            <option value="resultAt-asc">결과일 오래된순</option>
            <option value="myBidPrice-desc">금액 높은순</option>
            <option value="myBidPrice-asc">금액 낮은순</option>
          </select>
        </div>
        {hasFilter && (
          <button
            onClick={handleReset}
            className="text-xs text-neutral-500 hover:text-neutral-700 underline"
          >
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
          <button onClick={() => fetchWins(currentPage)} className="ml-auto text-xs underline hover:no-underline">
            다시 시도
          </button>
        </div>
      )}

      {/* 데스크톱 테이블 */}
      <div className="hidden md:block bg-white border border-neutral-200 rounded-lg overflow-hidden mb-4">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500">공고명</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 w-36">발주기관</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 w-28">추정가격</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 w-28">투찰가</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 w-24">낙찰률</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 w-28">결과일</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableSkeleton />
            ) : wins.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <EmptyState hasFilter={hasFilter} onReset={handleReset} />
                </td>
              </tr>
            ) : (
              wins.map((win) => (
                <tr
                  key={win.id}
                  className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/bids/${win.bidId}`}
                      className="text-sm font-medium text-neutral-800 hover:text-[#486581] line-clamp-1"
                    >
                      {win.title ?? `공고 ${win.bidId.slice(0, 8)}`}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-neutral-600">{win.organization ?? '-'}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-neutral-700">{formatAmount(win.budget)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-semibold text-neutral-800">
                      {formatAmount(win.myBidPrice)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-green-600 font-medium">
                      {win.bidRate != null ? formatWinRate(win.bidRate * 100) : '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-neutral-500">{formatDate(win.resultAt)}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 모바일 카드 */}
      <div className="md:hidden space-y-3 mb-4">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-white border border-neutral-200 rounded-lg p-4 animate-pulse">
              <div className="h-4 w-4/5 bg-neutral-200 rounded mb-2" />
              <div className="h-3 w-3/5 bg-neutral-100 rounded mb-2" />
              <div className="flex gap-3">
                <div className="h-3 w-16 bg-neutral-100 rounded" />
                <div className="h-3 w-16 bg-neutral-100 rounded" />
              </div>
            </div>
          ))
        ) : wins.length === 0 ? (
          <EmptyState hasFilter={hasFilter} onReset={handleReset} />
        ) : (
          wins.map((win) => (
            <div key={win.id} className="bg-white border border-neutral-200 rounded-lg p-4">
              <Link
                href={`/bids/${win.bidId}`}
                className="block text-sm font-medium text-neutral-800 hover:text-[#486581] line-clamp-1 mb-1"
              >
                {win.title ?? `공고 ${win.bidId.slice(0, 8)}`}
              </Link>
              {win.organization && (
                <p className="text-xs text-neutral-500 mb-2">{win.organization}</p>
              )}
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-xs text-neutral-500">
                  추정가: <span className="font-medium text-neutral-700">{formatAmount(win.budget)}</span>
                </span>
                <span className="text-xs text-neutral-500">
                  투찰가: <span className="font-semibold text-neutral-800">{formatAmount(win.myBidPrice)}</span>
                </span>
                {win.bidRate != null && (
                  <span className="text-xs font-medium text-green-600">
                    {formatWinRate(win.bidRate * 100)}
                  </span>
                )}
                <span className="text-xs text-neutral-400">{formatDate(win.resultAt)}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 페이지네이션 */}
      {!isLoading && wins.length > 0 && (
        <Pagination
          page={currentPage}
          totalPages={pagination.totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
