/**
 * F-10 알림 시스템 — 알림 Zustand 스토어
 * - 알림 목록, 안읽은 수 상태 관리
 * - 30초 폴링 (unread count), 탭 비활성 시 중지
 */
'use client';

import { create } from 'zustand';
import { notificationsApi } from '@/lib/api/notifications';
import type {
  Notification,
  NotificationListParams,
  NotificationSetting,
  UpdateNotificationSettingItem,
} from '@/types/notification';
import type { PaginationMeta } from '@/lib/api/client';

interface NotificationFilters {
  isRead?: boolean;
  type?: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

interface NotificationState {
  /** 알림 목록 */
  notifications: Notification[];
  /** 안읽은 알림 수 */
  unreadCount: number;
  /** 알림 목록 로딩 상태 */
  isLoading: boolean;
  /** 에러 메시지 */
  error: string | null;
  /** 페이지네이션 정보 */
  pagination: PaginationMeta;
  /** 현재 페이지 */
  currentPage: number;
  /** 필터 */
  filters: NotificationFilters;
  /** 폴링 타이머 ID */
  _pollingTimer: ReturnType<typeof setInterval> | null;
  /** 알림 설정 */
  settings: NotificationSetting[];
  /** 설정 로딩 상태 */
  isSettingsLoading: boolean;
}

interface NotificationActions {
  /** 알림 목록 조회 */
  fetchNotifications: (page?: number) => Promise<void>;
  /** 안읽은 알림 수 조회 */
  fetchUnreadCount: () => Promise<void>;
  /** 알림 읽음 처리 */
  markAsRead: (id: string) => Promise<void>;
  /** 전체 읽음 처리 */
  markAllAsRead: () => Promise<void>;
  /** 필터 설정 */
  setFilter: (key: keyof NotificationFilters, value: NotificationFilters[keyof NotificationFilters]) => void;
  /** 필터 초기화 */
  resetFilters: () => void;
  /** 페이지 변경 */
  setPage: (page: number) => void;
  /** 30초 폴링 시작 */
  startPolling: () => void;
  /** 폴링 중지 */
  stopPolling: () => void;
  /** 알림 설정 조회 */
  fetchSettings: () => Promise<void>;
  /** 알림 설정 변경 */
  updateSettings: (settings: UpdateNotificationSettingItem[]) => Promise<void>;
}

const defaultFilters: NotificationFilters = {
  isRead: undefined,
  type: undefined,
  sortBy: 'createdAt',
  sortOrder: 'desc',
};

const defaultPagination: PaginationMeta = {
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
};

export const useNotificationStore = create<NotificationState & NotificationActions>()((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,
  pagination: defaultPagination,
  currentPage: 1,
  filters: defaultFilters,
  _pollingTimer: null,
  settings: [],
  isSettingsLoading: false,

  fetchNotifications: async (page?: number) => {
    set({ isLoading: true, error: null });
    const { filters, currentPage } = get();
    const targetPage = page ?? currentPage;

    try {
      const params: NotificationListParams = {
        page: targetPage,
        pageSize: 20,
        isRead: filters.isRead,
        type: filters.type as NotificationListParams['type'],
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
      };
      const { items, meta } = await notificationsApi.getNotifications(params);
      set({
        notifications: items,
        pagination: meta,
        currentPage: targetPage,
        isLoading: false,
      });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({
        isLoading: false,
        error: error?.message ?? '알림 목록을 불러올 수 없습니다.',
      });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const count = await notificationsApi.getUnreadCount();
      set({ unreadCount: count });
    } catch {
      // 폴링 중 에러는 조용히 처리 (UI 방해 방지)
    }
  },

  markAsRead: async (id: string) => {
    try {
      await notificationsApi.markAsRead(id);
      // 로컬 상태 업데이트
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, isRead: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({ error: error?.message ?? '읽음 처리에 실패했습니다.' });
    }
  },

  markAllAsRead: async () => {
    try {
      await notificationsApi.markAllAsRead();
      // 로컬 상태 전체 읽음으로 업데이트
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, isRead: true })),
        unreadCount: 0,
      }));
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({ error: error?.message ?? '전체 읽음 처리에 실패했습니다.' });
    }
  },

  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      currentPage: 1,
    }));
  },

  resetFilters: () => {
    set({ filters: defaultFilters, currentPage: 1 });
  },

  setPage: (page) => {
    set({ currentPage: page });
  },

  startPolling: () => {
    const { _pollingTimer, fetchUnreadCount } = get();
    if (_pollingTimer) return; // 이미 폴링 중

    // 초기 조회
    fetchUnreadCount();

    const timer = setInterval(() => {
      // 탭 비활성 시 폴링 중지
      if (typeof document !== 'undefined' && document.hidden) return;
      fetchUnreadCount();
    }, 30_000); // 30초

    set({ _pollingTimer: timer });
  },

  stopPolling: () => {
    const { _pollingTimer } = get();
    if (_pollingTimer) {
      clearInterval(_pollingTimer);
      set({ _pollingTimer: null });
    }
  },

  fetchSettings: async () => {
    set({ isSettingsLoading: true });
    try {
      const settings = await notificationsApi.getSettings();
      set({ settings, isSettingsLoading: false });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({
        isSettingsLoading: false,
        error: error?.message ?? '알림 설정을 불러올 수 없습니다.',
      });
    }
  },

  updateSettings: async (newSettings: UpdateNotificationSettingItem[]) => {
    try {
      await notificationsApi.updateSettings({ settings: newSettings });
      // 로컬 상태 업데이트
      set((state) => ({
        settings: state.settings.map((s) => {
          const updated = newSettings.find((u) => u.notificationType === s.notificationType);
          if (!updated) return s;
          return {
            ...s,
            emailEnabled: updated.emailEnabled,
            kakaoEnabled: updated.kakaoEnabled,
            pushEnabled: updated.pushEnabled,
          };
        }),
      }));
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({ error: error?.message ?? '알림 설정 변경에 실패했습니다.' });
      throw err;
    }
  },
}));
