/**
 * 마감 임박 위젯
 * D-3 이하: error 색상, D-4~D-7: warning 색상
 */
import Link from 'next/link';
import type { UpcomingDeadline } from '@/types/dashboard';
import { PIPELINE_STATUS_LABELS } from '@/lib/stores/dashboard-store';

interface DeadlineWidgetProps {
  deadlines: UpcomingDeadline[];
  isLoading?: boolean;
}

function DeadlineBadge({ daysLeft }: { daysLeft: number }) {
  if (daysLeft <= 3) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-[#FFEBEE] text-[#C62828] whitespace-nowrap">
        D-{daysLeft <= 0 ? '0' : daysLeft}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-[#FFF8E1] text-[#F57C00] whitespace-nowrap">
      D-{daysLeft}
    </span>
  );
}

function DeadlineItemSkeleton() {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-neutral-100 last:border-0 animate-pulse">
      <div className="h-5 w-10 bg-neutral-200 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-1">
        <div className="h-3.5 w-4/5 bg-neutral-200 rounded" />
        <div className="h-3 w-2/5 bg-neutral-100 rounded" />
      </div>
    </div>
  );
}

export function DeadlineWidget({ deadlines, isLoading = false }: DeadlineWidgetProps) {
  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-neutral-700 flex items-center gap-1.5">
          <svg
            className="w-4 h-4 text-[#F57C00]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          마감 임박
        </h3>
        {!isLoading && deadlines.length > 0 && (
          <span className="text-xs text-neutral-400">{deadlines.length}건</span>
        )}
      </div>

      {/* 목록 */}
      {isLoading ? (
        <div>
          {[1, 2, 3].map((i) => (
            <DeadlineItemSkeleton key={i} />
          ))}
        </div>
      ) : deadlines.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-xs text-neutral-400">마감 임박 공고가 없습니다</p>
        </div>
      ) : (
        <div>
          {deadlines.map((item) => (
            <Link
              key={item.bidId}
              href={`/bids/${item.bidId}`}
              className="flex items-center gap-3 py-2 border-b border-neutral-100 last:border-0 hover:bg-neutral-50 -mx-1 px-1 rounded transition-colors"
            >
              <DeadlineBadge daysLeft={item.daysLeft} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-neutral-700 line-clamp-1">{item.title}</p>
                <p className="text-xs text-neutral-400 mt-0.5">
                  {PIPELINE_STATUS_LABELS[item.trackingStatus]}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
