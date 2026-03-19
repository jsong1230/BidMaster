/**
 * F-10 알림 시스템 — 헤더 알림 벨 컴포넌트
 * - unreadCount > 0 이면 빨간 뱃지 표시
 * - 클릭 시 드롭다운 (최근 5개 알림)
 * - "전체보기" 링크 → /notifications 페이지
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useNotificationStore } from '@/lib/stores/notification-store';
import { NotificationItem } from '@/components/notifications/NotificationItem';

export function NotificationBell() {
  const {
    unreadCount,
    notifications,
    isLoading,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    startPolling,
    stopPolling,
  } = useNotificationStore();

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 컴포넌트 마운트 시 폴링 시작
  useEffect(() => {
    startPolling();
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // ESC 키로 닫기
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false);
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => {
      if (!prev) {
        // 드롭다운 열 때 최신 알림 조회
        fetchNotifications(1);
      }
      return !prev;
    });
  }, [fetchNotifications]);

  const handleMarkAsRead = useCallback(
    async (id: string) => {
      await markAsRead(id);
      await fetchUnreadCount();
    },
    [markAsRead, fetchUnreadCount]
  );

  const handleMarkAllAsRead = useCallback(async () => {
    await markAllAsRead();
  }, [markAllAsRead]);

  // 드롭다운에 표시할 최근 5개
  const recentNotifications = notifications.slice(0, 5);
  const hasUnread = recentNotifications.some((n) => !n.isRead);

  return (
    <div ref={dropdownRef} className="relative">
      {/* 벨 버튼 */}
      <button
        onClick={handleToggle}
        aria-label={`알림${unreadCount > 0 ? ` (안읽은 알림 ${unreadCount}개)` : ''}`}
        className="relative p-2 rounded-md text-neutral-500 hover:text-neutral-800 hover:bg-neutral-100 transition-colors focus:outline-none focus:ring-2 focus:ring-[#486581] focus:ring-offset-1"
      >
        {/* 벨 아이콘 */}
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {/* 안읽음 뱃지 */}
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 min-w-[16px] h-4 px-0.5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center leading-none">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* 드롭다운 */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
          {/* 드롭다운 헤더 */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-100">
            <h3 className="text-sm font-semibold text-neutral-800">알림</h3>
            {hasUnread && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-xs text-[#486581] hover:text-[#334e68] font-medium transition-colors"
              >
                전체 읽음
              </button>
            )}
          </div>

          {/* 알림 목록 */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex flex-col gap-1 p-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex gap-3 p-2">
                    <div className="w-8 h-8 rounded-full bg-neutral-200 animate-pulse flex-shrink-0" />
                    <div className="flex-1 space-y-1.5">
                      <div className="h-3 w-3/5 bg-neutral-200 rounded animate-pulse" />
                      <div className="h-3 w-4/5 bg-neutral-200 rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recentNotifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <svg className="w-8 h-8 text-neutral-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <p className="text-xs text-neutral-400">새 알림이 없습니다</p>
              </div>
            ) : (
              <div className="divide-y divide-neutral-50">
                {recentNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={handleMarkAsRead}
                    compact
                  />
                ))}
              </div>
            )}
          </div>

          {/* 드롭다운 푸터 */}
          <div className="border-t border-neutral-100">
            <Link
              href="/notifications"
              onClick={() => setIsOpen(false)}
              className="block w-full px-4 py-3 text-xs font-medium text-center text-[#486581] hover:bg-neutral-50 transition-colors rounded-b-lg"
            >
              전체 알림 보기
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
