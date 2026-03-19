/**
 * KPI 카드 컴포넌트
 * 아이콘 + 숫자 + 라벨 + 서브텍스트
 */

interface KpiCardProps {
  icon: React.ReactNode;
  value: string;
  label: string;
  subText?: string;
  iconBgClass: string;
  iconColorClass: string;
  onClick?: () => void;
  isLoading?: boolean;
}

/** 스켈레톤 로딩 */
function KpiCardSkeleton() {
  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-6 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-neutral-200 rounded-lg animate-pulse flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-8 w-20 bg-neutral-200 rounded animate-pulse" />
          <div className="h-4 w-24 bg-neutral-100 rounded animate-pulse" />
          <div className="h-3 w-16 bg-neutral-100 rounded animate-pulse" />
        </div>
      </div>
    </div>
  );
}

export function KpiCard({
  icon,
  value,
  label,
  subText,
  iconBgClass,
  iconColorClass,
  onClick,
  isLoading = false,
}: KpiCardProps) {
  if (isLoading) return <KpiCardSkeleton />;

  return (
    <div
      className={`bg-white border border-neutral-200 rounded-lg p-6 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-shadow hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] ${
        onClick ? 'cursor-pointer' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      <div className="flex items-start gap-4">
        {/* 아이콘 */}
        <div
          className={`w-10 h-10 ${iconBgClass} rounded-lg flex items-center justify-center flex-shrink-0`}
        >
          <span className={iconColorClass}>{icon}</span>
        </div>
        {/* 수치 및 라벨 */}
        <div className="flex-1 min-w-0">
          <p className="text-[2rem] font-bold leading-[1.3] text-neutral-800 truncate">{value}</p>
          <p className="text-sm text-neutral-500 mt-0.5">{label}</p>
          {subText && <p className="text-xs text-neutral-400 mt-0.5">{subText}</p>}
        </div>
      </div>
    </div>
  );
}
