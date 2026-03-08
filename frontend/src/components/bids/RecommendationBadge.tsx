/**
 * 추천 등급 배지 컴포넌트
 */

import type { RecommendationType } from '@/types/bid-match';

interface RecommendationBadgeProps {
  recommendation: RecommendationType;
}

const RECOMMENDATION_CONFIG: Record<
  RecommendationType,
  { label: string; bgClass: string; textClass: string }
> = {
  recommended: {
    label: '추천',
    bgClass: 'bg-[#E8F5E9]',
    textClass: 'text-[#2E7D32]',
  },
  neutral: {
    label: '보통',
    bgClass: 'bg-[#FFF8E1]',
    textClass: 'text-[#F57C00]',
  },
  not_recommended: {
    label: '비추천',
    bgClass: 'bg-neutral-100',
    textClass: 'text-neutral-500',
  },
};

export function RecommendationBadge({ recommendation }: RecommendationBadgeProps) {
  const config = RECOMMENDATION_CONFIG[recommendation];

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${config.bgClass} ${config.textClass}`}
    >
      {config.label}
    </span>
  );
}
