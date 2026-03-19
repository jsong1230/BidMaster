/**
 * 파이프라인 칸반 컬럼 컴포넌트
 */
import { PipelineCard } from './PipelineCard';
import { PIPELINE_STATUS_COLORS, PIPELINE_STATUS_LABELS } from '@/lib/stores/dashboard-store';
import type { PipelineStage, TrackingStatusType } from '@/types/dashboard';

interface PipelineColumnProps {
  stage: PipelineStage;
  onStatusChange?: (bidId: string, newStatus: TrackingStatusType) => Promise<void>;
}

/** 스켈레톤 컬럼 */
export function PipelineColumnSkeleton() {
  return (
    <div className="flex-1 min-w-[220px] bg-neutral-50 rounded-lg border border-neutral-200 border-t-4 border-t-neutral-300">
      <div className="p-3 border-b border-neutral-200">
        <div className="flex items-center justify-between">
          <div className="h-4 w-12 bg-neutral-200 rounded animate-pulse" />
          <div className="h-5 w-6 bg-neutral-200 rounded-full animate-pulse" />
        </div>
      </div>
      <div className="p-3 space-y-2">
        {[1, 2].map((i) => (
          <div key={i} className="bg-white border border-neutral-200 rounded-lg p-3 animate-pulse">
            <div className="h-4 w-4/5 bg-neutral-200 rounded mb-2" />
            <div className="h-3 w-3/5 bg-neutral-100 rounded mb-2" />
            <div className="h-3 w-2/5 bg-neutral-100 rounded mb-3" />
            <div className="flex gap-1.5">
              <div className="h-5 w-10 bg-neutral-100 rounded" />
              <div className="h-5 w-8 bg-neutral-100 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PipelineColumn({ stage, onStatusChange }: PipelineColumnProps) {
  const colors = PIPELINE_STATUS_COLORS[stage.status];
  const isLost = stage.status === 'lost';

  return (
    <div
      className={`flex-1 min-w-[220px] bg-neutral-50 rounded-lg border border-neutral-200 border-t-4`}
      style={{ borderTopColor: getStatusHexColor(stage.status) }}
    >
      {/* 컬럼 헤더 */}
      <div className="p-3 border-b border-neutral-200 bg-white rounded-t-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-neutral-700">
            {PIPELINE_STATUS_LABELS[stage.status]}
          </span>
          <span
            className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold ${colors.badge}`}
          >
            {stage.count}
          </span>
        </div>
      </div>

      {/* 카드 목록 */}
      <div className="p-3 space-y-2 overflow-y-auto max-h-[calc(100vh-280px)]">
        {stage.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <svg
              className="w-8 h-8 text-neutral-300 mb-2"
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
            <p className="text-xs text-neutral-400">없음</p>
          </div>
        ) : (
          stage.items.map((item) => (
            <PipelineCard
              key={item.trackingId}
              item={item}
              currentStatus={stage.status}
              onStatusChange={onStatusChange}
              isLost={isLost}
            />
          ))
        )}
      </div>
    </div>
  );
}

function getStatusHexColor(status: TrackingStatusType): string {
  const map: Record<TrackingStatusType, string> = {
    interested: '#2196F3',
    participating: '#627D98',
    submitted: '#FFC107',
    won: '#4CAF50',
    lost: '#F44336',
  };
  return map[status];
}
