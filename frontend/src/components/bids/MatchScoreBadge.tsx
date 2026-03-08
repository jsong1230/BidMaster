/**
 * 매칭 점수 배지 컴포넌트
 * 70점 이상: 초록, 50~69: 노랑, 50 미만: 회색
 */

interface MatchScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

function getScoreStyle(score: number) {
  if (score >= 70) {
    return { bg: 'bg-[#E8F5E9]', text: 'text-[#2E7D32]' };
  }
  if (score >= 50) {
    return { bg: 'bg-[#FFF8E1]', text: 'text-[#F57C00]' };
  }
  return { bg: 'bg-[#F5F5F5]', text: 'text-[#616161]' };
}

export function MatchScoreBadge({ score, size = 'sm' }: MatchScoreBadgeProps) {
  const { bg, text } = getScoreStyle(score);

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5 font-bold',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-semibold ${bg} ${text} ${sizeClasses[size]}`}
    >
      {score.toFixed(1)}점
    </span>
  );
}
