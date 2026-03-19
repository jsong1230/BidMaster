/**
 * F-10 알림 시스템 — 알림 API 클라이언트
 */
import { apiClient } from './client';
import type { PaginationMeta } from './client';
import type {
  Notification,
  NotificationListParams,
  UnreadCountData,
  MarkReadData,
  MarkAllReadData,
  NotificationSetting,
  UpdateNotificationSettingsRequest,
  UpdateSettingsData,
} from '@/types/notification';

function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value));
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

export const notificationsApi = {
  /**
   * 알림 목록 조회
   * GET /api/v1/notifications
   */
  getNotifications: async (
    params?: NotificationListParams
  ): Promise<{ items: Notification[]; meta: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
      isRead: params?.isRead,
      type: params?.type,
      sortBy: params?.sortBy,
      sortOrder: params?.sortOrder,
    });
    const result = await apiClient.getList<Notification>(`/notifications${query}`);
    return {
      items: result.items,
      meta: result.meta ?? { page: 1, pageSize: 20, total: 0, totalPages: 0 },
    };
  },

  /**
   * 안읽은 알림 수 조회
   * GET /api/v1/notifications/unread-count
   */
  getUnreadCount: async (): Promise<number> => {
    const data = await apiClient.get<UnreadCountData>('/notifications/unread-count');
    return data.unreadCount;
  },

  /**
   * 알림 읽음 처리
   * PATCH /api/v1/notifications/{id}/read
   */
  markAsRead: async (id: string): Promise<MarkReadData> => {
    return apiClient.patch<MarkReadData>(`/notifications/${id}/read`);
  },

  /**
   * 전체 읽음 처리
   * POST /api/v1/notifications/read-all
   */
  markAllAsRead: async (): Promise<MarkAllReadData> => {
    return apiClient.post<MarkAllReadData>('/notifications/read-all');
  },

  /**
   * 알림 설정 조회
   * GET /api/v1/notifications/settings
   */
  getSettings: async (): Promise<NotificationSetting[]> => {
    const data = await apiClient.get<{ settings: NotificationSetting[] }>('/notifications/settings');
    return data.settings;
  },

  /**
   * 알림 설정 변경
   * PUT /api/v1/notifications/settings
   */
  updateSettings: async (request: UpdateNotificationSettingsRequest): Promise<UpdateSettingsData> => {
    return apiClient.put<UpdateSettingsData>('/notifications/settings', request);
  },
};
