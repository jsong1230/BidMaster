/**
 * F-10 알림 시스템 — 알림 아이템 컴포넌트
 * 알림 유형별 아이콘/색상, 읽음/안읽음 상태 표시
 */
'use client';

import type { Notification, NotificationType } from '@/types/notification';

/** 상대 시간 표시 ("방금 전", "3분 전", "1시간 전" 등) */
function formatRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return '방금 전';
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHour < 24) return `${diffHour}시간 전`;
  if (diffDay < 7) return `${diffDay}일 전`;
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

/** 알림 유형별 아이콘 및 색상 설정 */
function getTypeStyle(type: NotificationType): {
  icon: React.ReactNode;
  bgColor: string;
  iconColor: string;
} {
  switch (type) {
    case 'bid_matched':
      return {
        bgColor: 'bg-blue-50',
        iconColor: 'text-blue-500',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
            />
          </svg>
        ),
      };
    case 'deadline':
      return {
        bgColor: 'bg-amber-50',
        iconColor: 'text-amber-500',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        ),
      };
    case 'bid_result':
      return {
        bgColor: 'bg-green-50',
        iconColor: 'text-green-500',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        ),
      };
    case 'proposal_ready':
      return {
        bgColor: 'bg-purple-50',
        iconColor: 'text-purple-500',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        ),
      };
    default:
      return {
        bgColor: 'bg-neutral-50',
        iconColor: 'text-neutral-400',
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
        ),
      };
  }
}

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead?: (id: string) => void;
  /** compact: 드롭다운에서 사용 (더 작은 크기) */
  compact?: boolean;
}

export function NotificationItem({ notification, onMarkAsRead, compact = false }: NotificationItemProps) {
  const { icon, bgColor, iconColor } = getTypeStyle(notification.type);

  const handleClick = () => {
    if (!notification.isRead && onMarkAsRead) {
      onMarkAsRead(notification.id);
    }
  };

  return (
    <div
      className={`flex gap-3 ${compact ? 'p-3' : 'p-4'} cursor-pointer hover:bg-neutral-50 transition-colors ${
        !notification.isRead ? 'bg-blue-50/30' : ''
      }`}
      onClick={handleClick}
    >
      {/* 아이콘 */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full ${bgColor} ${iconColor} flex items-center justify-center`}>
        {icon}
      </div>

      {/* 내용 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={`font-medium text-neutral-800 leading-snug ${compact ? 'text-xs' : 'text-sm'} ${!notification.isRead ? 'font-semibold' : ''}`}>
            {notification.title}
          </p>
          {!notification.isRead && (
            <span className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-500 mt-1" />
          )}
        </div>
        <p className={`text-neutral-500 mt-0.5 line-clamp-2 leading-relaxed ${compact ? 'text-xs' : 'text-sm'}`}>
          {notification.content}
        </p>
        <p className={`text-neutral-400 mt-1 ${compact ? 'text-xs' : 'text-xs'}`}>
          {formatRelativeTime(notification.createdAt)}
        </p>
      </div>
    </div>
  );
}
