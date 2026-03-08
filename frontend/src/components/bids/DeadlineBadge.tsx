/**
 * 마감일 임박 배지 컴포넌트
 * D-3 이하: 빨간 배지
 * D-4~D-7: 노란 배지
 * D-8 이상: 미표시
 */

interface DeadlineBadgeProps {
  deadline: string;
}

function getDaysLeft(deadline: string): number {
  const now = new Date();
  const deadlineDate = new Date(deadline);
  const diffMs = deadlineDate.getTime() - now.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

export function DeadlineBadge({ deadline }: DeadlineBadgeProps) {
  const daysLeft = getDaysLeft(deadline);

  if (daysLeft > 7) return null;

  if (daysLeft <= 3) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-[#FFEBEE] text-[#C62828]">
        {daysLeft <= 0 ? 'D-0' : `D-${daysLeft}`}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-[#FFF8E1] text-[#F57C00]">
      D-{daysLeft}
    </span>
  );
}
