/**
 * 입찰 파이프라인 페이지
 * 5열 칸반 보드 + 상태 변경 + 30초 폴링
 */
'use client';

import { useCallback, useEffect } from 'react';
import { PipelineBoard } from '@/components/dashboard/PipelineBoard';
import { useDashboardStore } from '@/lib/stores/dashboard-store';
import { showToast } from '@/components/ui/Toast';
import type { TrackingStatusType, TrackingUpsertRequest } from '@/types/dashboard';

export default function PipelinePage() {
  const {
    pipeline,
    isLoadingPipeline,
    errorPipeline,
    fetchPipeline,
    updateTrackingStatus,
    startPolling,
    stopPolling,
  } = useDashboardStore();

  useEffect(() => {
    fetchPipeline();
    startPolling();
    return () => stopPolling();
  }, [fetchPipeline, startPolling, stopPolling]);

  const totalCount = pipeline?.stages.reduce((sum, s) => sum + s.count, 0) ?? 0;

  const handleStatusChange = useCallback(
    async (bidId: string, newStatus: TrackingStatusType) => {
      try {
        const data: TrackingUpsertRequest = { status: newStatus };
        await updateTrackingStatus(bidId, data);
        showToast('상태가 변경되었습니다.');
      } catch {
        showToast('상태 변경에 실패했습니다.', 'error');
      }
    },
    [updateTrackingStatus]
  );

  return (
    <div className="p-6 max-w-screen-2xl mx-auto">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-neutral-800">입찰 파이프라인</h1>
          {!isLoadingPipeline && (
            <p className="text-sm text-neutral-500 mt-0.5">
              총 <span className="font-semibold text-neutral-700">{totalCount}건</span> 추적 중
            </p>
          )}
        </div>
        <button
          onClick={() => fetchPipeline()}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-neutral-200 rounded-md text-neutral-600 hover:bg-neutral-50 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          새로고침
        </button>
      </div>

      {/* 에러 */}
      {errorPipeline && !isLoadingPipeline && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-[#FFEBEE] border border-[#FFCDD2] rounded-lg text-sm text-[#C62828]">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {errorPipeline}
          <button
            onClick={() => fetchPipeline()}
            className="ml-auto text-xs underline hover:no-underline"
          >
            다시 시도
          </button>
        </div>
      )}

      {/* 칸반 보드 */}
      <PipelineBoard
        pipeline={pipeline}
        isLoading={isLoadingPipeline}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
}
