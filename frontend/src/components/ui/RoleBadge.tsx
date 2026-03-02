import type { MemberRole } from '@/types/company';

interface RoleBadgeProps {
  role: MemberRole;
}

const roleConfig: Record<MemberRole, { label: string; className: string }> = {
  owner: {
    label: '소유자',
    className: 'bg-purple-100 text-purple-700',
  },
  admin: {
    label: '관리자',
    className: 'bg-blue-100 text-blue-700',
  },
  member: {
    label: '멤버',
    className: 'bg-neutral-100 text-neutral-600',
  },
};

/**
 * 멤버 역할 배지 컴포넌트
 */
export default function RoleBadge({ role }: RoleBadgeProps) {
  const config = roleConfig[role];
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${config.className}`}
    >
      {config.label}
    </span>
  );
}
