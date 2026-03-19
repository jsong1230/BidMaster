/**
 * F-10 알림 시스템 — TypeScript 타입 정의
 */

/** 알림 유형 */
export type NotificationType = 'bid_matched' | 'deadline' | 'bid_result' | 'proposal_ready';

/** 알림 채널 */
export type NotificationChannel = 'in_app' | 'email' | 'kakao';

/** 알림 단건 */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  content: string;
  data: Record<string, unknown>;
  isRead: boolean;
  channel: NotificationChannel;
  sentAt: string | null;
  readAt: string | null;
  createdAt: string;
}

/** 알림 목록 응답 data 필드 */
export interface NotificationListData {
  items: Notification[];
}

/** 안읽은 알림 수 응답 data 필드 */
export interface UnreadCountData {
  unreadCount: number;
}

/** 읽음 처리 응답 data 필드 */
export interface MarkReadData {
  id: string;
  isRead: boolean;
  readAt: string;
}

/** 전체 읽음 처리 응답 data 필드 */
export interface MarkAllReadData {
  updatedCount: number;
}

/** 알림 설정 단건 */
export interface NotificationSetting {
  notificationType: NotificationType;
  label: string;
  emailEnabled: boolean;
  kakaoEnabled: boolean;
  pushEnabled: boolean;
}

/** 알림 설정 목록 응답 data 필드 */
export interface NotificationSettingsData {
  settings: NotificationSetting[];
}

/** 알림 설정 변경 요청 단건 */
export interface UpdateNotificationSettingItem {
  notificationType: NotificationType;
  emailEnabled: boolean;
  kakaoEnabled: boolean;
  pushEnabled: boolean;
}

/** 알림 설정 변경 요청 바디 */
export interface UpdateNotificationSettingsRequest {
  settings: UpdateNotificationSettingItem[];
}

/** 알림 설정 변경 응답 data 필드 */
export interface UpdateSettingsData {
  updatedCount: number;
}

/** 알림 목록 조회 파라미터 */
export interface NotificationListParams {
  page?: number;
  pageSize?: number;
  isRead?: boolean;
  type?: NotificationType;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}
