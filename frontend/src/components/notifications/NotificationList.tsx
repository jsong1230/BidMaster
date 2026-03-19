/**
 * F-10 알림 시스템 — 알림 목록 컴포넌트
 * 필터 탭, 페이지네이션 포함
 */
'use client';

import { useCallback, useEffect } from 'react';
import { useNotificationStore } from '@/lib/stores/notification-store';
import { NotificationItem } from './NotificationItem';
import type { NotificationType } from '@/types/notification';

/** 필터 탭 옵션 */
const TYPE_FILTERS: Array<{ value: string; label: string }> = [
  { value: '', label: '전체' },
  { value: 'bid_matched', label: '매칭 공고' },
  { value: 'deadline', label: '마감 임박' },
  { value: 'bid_result', label: '낙찰 결과' },
  { value: 'proposal_ready', label: '제안서 완료' },
];

const READ_FILTERS: Array<{ value: string; label: string }> = [
  { value: '', label: '전체' },
  { value: 'false', label: '안읽음' },
  { value: 'true', label: '읽음' },
];

/** 스켈레톤 로딩 */
function NotificationSkeleton() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex gap-3 p-4 border-b border-neutral-100 last:border-0">
          <div className="w-8 h-8 rounded-full bg-neutral-200 animate-pulse flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-3/5 bg-neutral-200 rounded animate-pulse" />
            <div className="h-3 w-4/5 bg-neutral-200 rounded animate-pulse" />
            <div className="h-3 w-1/4 bg-neutral-200 rounded animate-pulse" />
          </div>
        </div>
      ))}
    </>
  );
}

/** 빈 상태 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-neutral-100 flex items-center justify-center mb-4">
        <svg className="w-6 h-6 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
      </div>
      <p className="text-sm font-semibold text-neutral-700 mb-1">알림이 없습니다</p>
      <p className="text-xs text-neutral-400">새로운 알림이 오면 여기에 표시됩니다</p>
    </div>
  );
}

/** 페이지네이션 */
function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex items-center justify-center gap-1 py-4">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md disabled:opacity-40 hover:bg-neutral-50 transition-colors"
      >
        이전
      </button>
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`w-9 h-9 text-sm rounded-md transition-colors ${
            p === page
              ? 'bg-[#486581] text-white font-semibold'
              : 'border border-neutral-200 text-neutral-600 hover:bg-neutral-50'
          }`}
        >
          {p}
        </button>
      ))}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md disabled:opacity-40 hover:bg-neutral-50 transition-colors"
      >
        다음
      </button>
    </div>
  );
}

export function NotificationList() {
  const {
    notifications,
    isLoading,
    error,
    pagination,
    filters,
    currentPage,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    setFilter,
    resetFilters,
    setPage,
  } = useNotificationStore();

  // 초기 로드 및 필터/페이지 변경 시 재조회
  useEffect(() => {
    fetchNotifications(currentPage);
  }, [fetchNotifications, currentPage, filters]);

  const handlePageChange = useCallback(
    (page: number) => {
      setPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    [setPage]
  );

  const handleMarkAsRead = useCallback(
    async (id: string) => {
      await markAsRead(id);
    },
    [markAsRead]
  );

  const handleMarkAllAsRead = useCallback(async () => {
    await markAllAsRead();
    await fetchUnreadCount();
  }, [markAllAsRead, fetchUnreadCount]);

  const handleTypeFilter = useCallback(
    (value: string) => {
      setFilter('type', value === '' ? undefined : (value as NotificationType));
    },
    [setFilter]
  );

  const handleReadFilter = useCallback(
    (value: string) => {
      if (value === '') {
        setFilter('isRead', undefined);
      } else {
        setFilter('isRead', value === 'true');
      }
    },
    [setFilter]
  );

  const currentReadFilter =
    filters.isRead === undefined ? '' : filters.isRead ? 'true' : 'false';
  const currentTypeFilter = filters.type ?? '';

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <div>
      {/* 필터 + 전체 읽음 버튼 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex flex-wrap gap-2">
          {/* 유형 필터 탭 */}
          <div className="flex bg-neutral-100 rounded-lg p-0.5 gap-0.5">
            {TYPE_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => handleTypeFilter(f.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  currentTypeFilter === f.value
                    ? 'bg-white text-neutral-800 shadow-sm'
                    : 'text-neutral-500 hover:text-neutral-700'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* 읽음 필터 탭 */}
          <div className="flex bg-neutral-100 rounded-lg p-0.5 gap-0.5">
            {READ_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => handleReadFilter(f.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  currentReadFilter === f.value
                    ? 'bg-white text-neutral-800 shadow-sm'
                    : 'text-neutral-500 hover:text-neutral-700'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {(currentTypeFilter || currentReadFilter) && (
            <button
              onClick={resetFilters}
              className="text-xs text-neutral-400 hover:text-neutral-600 transition-colors"
            >
              필터 초기화
            </button>
          )}
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="px-3 py-1.5 text-xs font-medium text-[#486581] border border-[#486581]/30 rounded-md hover:bg-[#486581]/5 transition-colors"
            >
              전체 읽음 처리
            </button>
          )}
        </div>
      </div>

      {/* 에러 상태 */}
      {error && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {error}
          <button
            onClick={() => fetchNotifications(currentPage)}
            className="ml-auto text-xs underline hover:no-underline"
          >
            다시 시도
          </button>
        </div>
      )}

      {/* 알림 목록 */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        {isLoading ? (
          <NotificationSkeleton />
        ) : notifications.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="divide-y divide-neutral-100">
            {notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkAsRead={handleMarkAsRead}
              />
            ))}
          </div>
        )}
      </div>

      {/* 페이지네이션 */}
      {!isLoading && notifications.length > 0 && (
        <Pagination
          page={currentPage}
          totalPages={pagination.totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
