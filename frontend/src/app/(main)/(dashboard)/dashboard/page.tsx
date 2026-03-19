/**
 * 대시보드 홈 페이지
 * KPI 4열 + 파이프라인 미니뷰 + 마감 임박 + 차트
 * 30초 폴링 (summary + pipeline)
 */
'use client';

import { useCallback, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { DeadlineWidget } from '@/components/dashboard/DeadlineWidget';
import { WinRateTrend } from '@/components/dashboard/WinRateTrend';
import { StatisticsChart } from '@/components/dashboard/StatisticsChart';
import { useDashboardStore, PERIOD_OPTIONS, PIPELINE_STATUS_LABELS, PIPELINE_STATUS_COLORS } from '@/lib/stores/dashboard-store';
import { formatAmount, formatWinRate } from '@/lib/utils/format';

/** 파이프라인 미니뷰: 가로 막대형 + 최근 아이템 */
function PipelineMiniView() {
  const { pipeline, isLoadingPipeline, errorPipeline, fetchPipeline } = useDashboardStore();

  const totalCount = pipeline?.stages.reduce((sum, s) => sum + s.count, 0) ?? 0;

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-neutral-700">입찰 파이프라인</h3>
        <Link
          href="/pipeline"
          className="text-xs text-[#486581] hover:underline flex items-center gap-0.5"
        >
          전체보기
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>

      {errorPipeline ? (
        <div className="py-4 text-center">
          <p className="text-xs text-neutral-400 mb-2">{errorPipeline}</p>
          <button
            onClick={() => fetchPipeline()}
            className="text-xs text-[#486581] hover:underline"
          >
            다시 시도
          </button>
        </div>
      ) : isLoadingPipeline ? (
        <div className="space-y-2">
          <div className="h-6 bg-neutral-100 rounded animate-pulse" />
          <div className="h-4 w-4/5 bg-neutral-100 rounded animate-pulse" />
          <div className="h-4 w-3/5 bg-neutral-100 rounded animate-pulse" />
        </div>
      ) : pipeline ? (
        <>
          {/* 가로 막대형 카운트 */}
          <div className="flex gap-2 mb-4 flex-wrap">
            {pipeline.stages.map((stage) => {
              const colors = PIPELINE_STATUS_COLORS[stage.status];
              return (
                <div
                  key={stage.status}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${colors.badge}`}
                >
                  {PIPELINE_STATUS_LABELS[stage.status]}
                  <span className="font-bold">{stage.count}</span>
                </div>
              );
            })}
          </div>

          {/* 최근 변경 3건 */}
          {totalCount > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs font-medium text-neutral-500 mb-1">최근 변경</p>
              {pipeline.stages
                .flatMap((s) =>
                  s.items.map((item) => ({ ...item, status: s.status }))
                )
                .sort(
                  (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
                )
                .slice(0, 3)
                .map((item) => {
                  const colors = PIPELINE_STATUS_COLORS[item.status];
                  return (
                    <Link
                      key={item.trackingId}
                      href={`/bids/${item.bidId}`}
                      className="flex items-center gap-2 py-1 hover:bg-neutral-50 -mx-1 px-1 rounded transition-colors"
                    >
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${colors.badge}`}
                      >
                        {PIPELINE_STATUS_LABELS[item.status]}
                      </span>
                      <span className="text-xs text-neutral-700 line-clamp-1 flex-1">
                        {item.title}
                      </span>
                      {item.daysLeft <= 7 && (
                        <span
                          className={`text-xs flex-shrink-0 ${
                            item.daysLeft <= 3 ? 'text-[#C62828]' : 'text-[#F57C00]'
                          }`}
                        >
                          D-{item.daysLeft}
                        </span>
                      )}
                    </Link>
                  );
                })}
            </div>
          )}

          {totalCount === 0 && (
            <p className="text-xs text-neutral-400 py-4 text-center">
              공고에 관심을 표시하면 파이프라인이 시작됩니다
            </p>
          )}
        </>
      ) : null}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const {
    summary,
    statistics,
    isLoadingSummary,
    isLoadingStats,
    errorSummary,
    errorStats,
    selectedPeriod,
    fetchAll,
    fetchStatistics,
    setPeriod,
    startPolling,
    stopPolling,
  } = useDashboardStore();

  // 초기 로드 및 폴링 시작
  useEffect(() => {
    fetchAll();
    startPolling();
    return () => stopPolling();
  }, [fetchAll, startPolling, stopPolling]);

  const handlePeriodChange = useCallback(
    (period: string) => {
      setPeriod(period);
    },
    [setPeriod]
  );

  const handleRetryStats = useCallback(() => {
    fetchStatistics(6);
  }, [fetchStatistics]);

  return (
    <div className="p-6 max-w-screen-xl mx-auto">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-neutral-800">대시보드</h1>
          <p className="text-sm text-neutral-500 mt-0.5">입찰 현황을 한눈에 확인하세요</p>
        </div>
        {/* 기간 선택 */}
        <select
          value={selectedPeriod}
          onChange={(e) => handlePeriodChange(e.target.value)}
          className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-[#486581] focus:border-transparent"
        >
          {PERIOD_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* 에러 (summary) */}
      {errorSummary && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#FFEBEE] border border-[#FFCDD2] rounded-lg text-sm text-[#C62828]">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {errorSummary}
        </div>
      )}

      {/* KPI 카드 그리드 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* 참여 공고 */}
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          value={String(summary?.participationCount ?? 0)}
          label="이번 달 참여"
          iconBgClass="bg-blue-50"
          iconColorClass="text-blue-500"
          isLoading={isLoadingSummary}
        />

        {/* 제출 완료 */}
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          }
          value={String(summary?.submissionCount ?? 0)}
          label="제출 완료"
          iconBgClass="bg-[#F0F4F8]"
          iconColorClass="text-[#627D98]"
          isLoading={isLoadingSummary}
        />

        {/* 낙찰 */}
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          }
          value={String(summary?.wonCount ?? 0)}
          label="낙찰"
          subText={summary?.totalWonAmount ? formatAmount(summary.totalWonAmount) : undefined}
          iconBgClass="bg-green-50"
          iconColorClass="text-green-500"
          onClick={() => router.push('/bids/wins')}
          isLoading={isLoadingSummary}
        />

        {/* 낙찰률 */}
        <KpiCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
          value={formatWinRate(summary?.winRate ?? 0)}
          label="낙찰률"
          iconBgClass="bg-[#ECEFF1]"
          iconColorClass="text-[#78909C]"
          isLoading={isLoadingSummary}
        />
      </div>

      {/* 2열 콘텐츠 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
        {/* 좌측: 파이프라인 미니뷰 (3/5) */}
        <div className="lg:col-span-3">
          <PipelineMiniView />
        </div>

        {/* 우측: 마감 임박 + 낙찰률 추이 (2/5) */}
        <div className="lg:col-span-2 space-y-4">
          <DeadlineWidget
            deadlines={summary?.upcomingDeadlines ?? []}
            isLoading={isLoadingSummary}
          />
          <WinRateTrend
            data={statistics?.monthly ?? []}
            isLoading={isLoadingStats}
          />
        </div>
      </div>

      {/* 통계 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <StatisticsChart
          data={statistics?.monthly ?? []}
          isLoading={isLoadingStats}
        />

        {/* 누적 통계 요약 */}
        {!isLoadingStats && statistics && (
          <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-neutral-700">누적 성과</h3>
              <button
                onClick={handleRetryStats}
                className="text-xs text-[#486581] hover:underline"
              >
                새로고침
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: '총 참여', value: `${statistics.cumulative.totalParticipation}건` },
                { label: '총 낙찰', value: `${statistics.cumulative.totalWon}건` },
                {
                  label: '총 낙찰금액',
                  value: formatAmount(statistics.cumulative.totalWonAmount),
                },
                {
                  label: '전체 낙찰률',
                  value: formatWinRate(statistics.cumulative.overallWinRate),
                },
              ].map((item) => (
                <div key={item.label} className="bg-neutral-50 rounded-lg p-3">
                  <p className="text-xs text-neutral-500 mb-1">{item.label}</p>
                  <p className="text-base font-bold text-neutral-800">{item.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {errorStats && (
          <div className="bg-white border border-neutral-200 rounded-lg p-4 flex flex-col items-center justify-center gap-2">
            <p className="text-sm text-neutral-500">데이터를 불러올 수 없습니다.</p>
            <button
              onClick={handleRetryStats}
              className="text-xs text-[#486581] hover:underline"
            >
              다시 시도
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
