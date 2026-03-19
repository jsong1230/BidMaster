/**
 * 파이프라인 칸반 카드 컴포넌트
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { formatAmount, formatDate } from '@/lib/utils/format';
import { PIPELINE_STATUS_LABELS, PIPELINE_STATUS_COLORS } from '@/lib/stores/dashboard-store';
import type { PipelineItem, TrackingStatusType } from '@/types/dashboard';

const ALL_STATUSES: TrackingStatusType[] = [
  'interested',
  'participating',
  'submitted',
  'won',
  'lost',
];

interface PipelineCardProps {
  item: PipelineItem;
  currentStatus: TrackingStatusType;
  onStatusChange?: (bidId: string, newStatus: TrackingStatusType) => Promise<void>;
  isLost?: boolean;
}

/** D-day 배지 */
function DaysBadge({ daysLeft }: { daysLeft: number }) {
  if (daysLeft <= 0) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-[#FFEBEE] text-[#C62828]">
        D+{Math.abs(daysLeft)}
      </span>
    );
  }
  if (daysLeft <= 3) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-[#FFEBEE] text-[#C62828]">
        D-{daysLeft}
      </span>
    );
  }
  if (daysLeft <= 7) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-[#FFF8E1] text-[#F57C00]">
        D-{daysLeft}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-neutral-100 text-neutral-500">
      D-{daysLeft}
    </span>
  );
}

/** 상태 변경 드롭다운 */
function StatusDropdown({
  currentStatus,
  bidId,
  onStatusChange,
}: {
  currentStatus: TrackingStatusType;
  bidId: string;
  onStatusChange?: (bidId: string, newStatus: TrackingStatusType) => Promise<void>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleSelect = async (newStatus: TrackingStatusType) => {
    if (newStatus === currentStatus || !onStatusChange) return;
    setIsOpen(false);
    setIsUpdating(true);
    try {
      await onStatusChange(bidId, newStatus);
    } finally {
      setIsUpdating(false);
    }
  };

  const colors = PIPELINE_STATUS_COLORS[currentStatus];

  return (
    <div className="relative">
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        disabled={isUpdating}
        className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium border transition-colors ${colors.badge} border-transparent hover:opacity-80 disabled:opacity-50`}
      >
        {isUpdating ? (
          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : null}
        {PIPELINE_STATUS_LABELS[currentStatus]}
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* 오버레이 */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 top-full mt-1 z-20 bg-white border border-neutral-200 rounded-lg shadow-lg py-1 min-w-[100px]">
            {ALL_STATUSES.map((status) => {
              const c = PIPELINE_STATUS_COLORS[status];
              return (
                <button
                  key={status}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelect(status);
                  }}
                  className={`w-full text-left px-3 py-1.5 text-xs hover:bg-neutral-50 transition-colors ${
                    status === currentStatus ? 'font-semibold' : ''
                  } ${c.text}`}
                >
                  {PIPELINE_STATUS_LABELS[status]}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

export function PipelineCard({ item, currentStatus, onStatusChange, isLost = false }: PipelineCardProps) {
  return (
    <div
      className={`bg-white border border-neutral-200 rounded-lg p-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-shadow ${
        isLost ? 'opacity-60' : ''
      }`}
    >
      {/* 공고명 */}
      <Link
        href={`/bids/${item.bidId}`}
        className="block text-sm font-medium text-neutral-800 hover:text-[#486581] line-clamp-1 mb-1.5"
        title={item.title}
      >
        {item.title}
      </Link>

      {/* 기관명 */}
      <p className="text-xs text-neutral-500 mb-2 line-clamp-1">{item.organization}</p>

      {/* 예산 */}
      <p className="text-xs font-semibold text-neutral-700 mb-2">
        {formatAmount(item.budget)}
      </p>

      {/* 투찰가 (submitted 이후) */}
      {item.myBidPrice != null && (
        <p className="text-xs text-neutral-500 mb-2">
          투찰가: <span className="font-medium text-neutral-700">{formatAmount(item.myBidPrice)}</span>
        </p>
      )}

      {/* 마감일 D-day + 매칭점수 */}
      <div className="flex items-center gap-1.5 mb-2.5 flex-wrap">
        <DaysBadge daysLeft={item.daysLeft} />
        {item.totalScore != null && (
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-neutral-100 text-neutral-600">
            {item.totalScore.toFixed(1)}점
          </span>
        )}
      </div>

      {/* 상태 드롭다운 */}
      <div className="flex items-center justify-between">
        <StatusDropdown
          currentStatus={currentStatus}
          bidId={item.bidId}
          onStatusChange={onStatusChange}
        />
        {/* 최종 업데이트 */}
        <span className="text-xs text-neutral-400">{formatDate(item.updatedAt)}</span>
      </div>
    </div>
  );
}
