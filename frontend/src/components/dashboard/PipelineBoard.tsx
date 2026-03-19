/**
 * 파이프라인 칸반 보드 컴포넌트
 * 데스크톱: 5열 균등 / 모바일: 탭 전환
 */
'use client';

import { useState } from 'react';
import { PipelineColumn, PipelineColumnSkeleton } from './PipelineColumn';
import { PIPELINE_STATUS_LABELS, PIPELINE_STATUS_COLORS } from '@/lib/stores/dashboard-store';
import type { PipelineData, TrackingStatusType } from '@/types/dashboard';

const TAB_ORDER: TrackingStatusType[] = [
  'interested',
  'participating',
  'submitted',
  'won',
  'lost',
];

interface PipelineBoardProps {
  pipeline: PipelineData | null;
  isLoading: boolean;
  onStatusChange?: (bidId: string, newStatus: TrackingStatusType) => Promise<void>;
}

export function PipelineBoard({ pipeline, isLoading, onStatusChange }: PipelineBoardProps) {
  const [activeTab, setActiveTab] = useState<TrackingStatusType>('interested');

  if (isLoading) {
    return (
      <>
        {/* 데스크톱 스켈레톤 */}
        <div className="hidden lg:flex gap-3">
          {TAB_ORDER.map((status) => (
            <PipelineColumnSkeleton key={status} />
          ))}
        </div>
        {/* 모바일 스켈레톤 */}
        <div className="lg:hidden">
          <PipelineColumnSkeleton />
        </div>
      </>
    );
  }

  if (!pipeline) return null;

  const totalCount = pipeline.stages.reduce((sum, s) => sum + s.count, 0);

  // 빈 파이프라인
  if (totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <svg
          className="w-16 h-16 text-neutral-300 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <p className="text-sm font-semibold text-neutral-700 mb-1">
          아직 추적 중인 입찰이 없습니다
        </p>
        <p className="text-xs text-neutral-400 mb-4">
          공고에 관심을 표시하면 파이프라인이 시작됩니다
        </p>
        <a
          href="/bids"
          className="px-4 py-2 text-sm font-medium bg-[#486581] text-white rounded-md hover:bg-[#334E68] transition-colors"
        >
          공고 목록으로 이동
        </a>
      </div>
    );
  }

  return (
    <>
      {/* 데스크톱: 5열 가로 배치 */}
      <div className="hidden lg:flex gap-3 overflow-x-auto pb-4">
        {pipeline.stages.map((stage) => (
          <PipelineColumn
            key={stage.status}
            stage={stage}
            onStatusChange={onStatusChange}
          />
        ))}
      </div>

      {/* 모바일: 탭 전환 */}
      <div className="lg:hidden">
        {/* 탭 헤더 */}
        <div className="flex gap-1 mb-3 overflow-x-auto pb-1">
          {pipeline.stages.map((stage) => {
            const colors = PIPELINE_STATUS_COLORS[stage.status];
            const isActive = activeTab === stage.status;
            return (
              <button
                key={stage.status}
                onClick={() => setActiveTab(stage.status)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0 ${
                  isActive
                    ? `${colors.badge} ring-1 ring-current`
                    : 'bg-neutral-100 text-neutral-500 hover:bg-neutral-200'
                }`}
              >
                {PIPELINE_STATUS_LABELS[stage.status]}
                <span
                  className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold ${
                    isActive ? '' : 'bg-neutral-200 text-neutral-600'
                  }`}
                >
                  {stage.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* 선택된 탭 컬럼 */}
        {pipeline.stages
          .filter((s) => s.status === activeTab)
          .map((stage) => (
            <PipelineColumn
              key={stage.status}
              stage={stage}
              onStatusChange={onStatusChange}
            />
          ))}
      </div>
    </>
  );
}
