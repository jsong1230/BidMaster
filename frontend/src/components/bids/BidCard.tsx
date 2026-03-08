/**
 * 공고 카드 컴포넌트 (모바일 카드뷰)
 */

import Link from 'next/link';
import type { BidItem } from '@/types/bid';
import { BidStatusBadge } from './BidStatusBadge';
import { DeadlineBadge } from './DeadlineBadge';
import { MatchScoreBadge } from './MatchScoreBadge';

interface BidCardProps {
  bid: BidItem;
  matchScore?: number;
}

function formatBudget(budget?: number): string {
  if (!budget) return '-';
  if (budget >= 100_000_000) {
    return `${(budget / 100_000_000).toFixed(0)}억원`;
  }
  if (budget >= 10_000) {
    return `${(budget / 10_000).toFixed(0)}만원`;
  }
  return `${budget.toLocaleString()}원`;
}

function formatDeadline(deadline: string): string {
  const date = new Date(deadline);
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

export function BidCard({ bid, matchScore }: BidCardProps) {
  return (
    <Link href={`/bids/${bid.id}`}>
      <div className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
        {/* 상태 배지 + 마감일 */}
        <div className="flex items-center gap-2 mb-2">
          <BidStatusBadge status={bid.status} />
          <DeadlineBadge deadline={bid.deadline} />
          {matchScore !== undefined && <MatchScoreBadge score={matchScore} />}
        </div>

        {/* 공고명 */}
        <h3 className="text-sm font-semibold text-neutral-800 mb-2 line-clamp-2 leading-snug">
          {bid.title}
        </h3>

        {/* 메타 정보 */}
        <div className="space-y-1 text-xs text-neutral-500">
          <div className="flex items-center gap-1">
            <span className="text-neutral-400">발주기관</span>
            <span className="font-medium text-neutral-700">{bid.organization}</span>
          </div>
          {bid.category && (
            <div className="flex items-center gap-1">
              <span className="text-neutral-400">분류</span>
              <span>{bid.category}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="text-neutral-400">예산</span>
              <span className="font-medium">{formatBudget(bid.budget)}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-neutral-400">마감</span>
              <span>{formatDeadline(bid.deadline)}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
