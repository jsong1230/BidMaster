/**
 * F-10 알림 시스템 — 알림 목록 페이지
 * /notifications
 */
import { NotificationList } from '@/components/notifications/NotificationList';

export default function NotificationsPage() {
  return (
    <div className="p-6 max-w-screen-md mx-auto">
      {/* 페이지 헤더 */}
      <div className="mb-5">
        <h1 className="text-xl font-bold text-neutral-800">알림</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          매칭 공고, 마감 임박, 낙찰 결과 등 알림을 확인하세요
        </p>
      </div>

      <NotificationList />
    </div>
  );
}
