/**
 * 매칭 점수 + 추천 등급 통합 배지 컴포넌트
 */

import type { RecommendationType } from '@/types/bid-match';
import { MatchScoreBadge } from './MatchScoreBadge';
import { RecommendationBadge } from './RecommendationBadge';

interface BidMatchBadgeProps {
  totalScore: number;
  recommendation: RecommendationType;
  size?: 'sm' | 'md';
}

export function BidMatchBadge({ totalScore, recommendation, size = 'sm' }: BidMatchBadgeProps) {
  return (
    <div className="flex items-center gap-1.5">
      <MatchScoreBadge score={totalScore} size={size} />
      <RecommendationBadge recommendation={recommendation} />
    </div>
  );
}
