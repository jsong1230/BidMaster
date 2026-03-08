/**
 * 공고 상태 배지 컴포넌트
 */

import type { BidStatus } from '@/types/bid';

interface BidStatusBadgeProps {
  status: BidStatus;
}

const STATUS_CONFIG: Record<BidStatus, { label: string; bgClass: string; textClass: string; dotClass: string }> = {
  open: {
    label: '모집중',
    bgClass: 'bg-[#E3F2FD]',
    textClass: 'text-[#1565C0]',
    dotClass: 'bg-[#2196F3]',
  },
  closed: {
    label: '마감',
    bgClass: 'bg-neutral-100',
    textClass: 'text-neutral-500',
    dotClass: 'bg-neutral-400',
  },
  awarded: {
    label: '낙찰',
    bgClass: 'bg-[#E8F5E9]',
    textClass: 'text-[#2E7D32]',
    dotClass: 'bg-[#4CAF50]',
  },
  cancelled: {
    label: '취소',
    bgClass: 'bg-[#FFEBEE]',
    textClass: 'text-[#C62828]',
    dotClass: 'bg-[#F44336]',
  },
};

export function BidStatusBadge({ status }: BidStatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${config.bgClass} ${config.textClass}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass}`} />
      {config.label}
    </span>
  );
}
