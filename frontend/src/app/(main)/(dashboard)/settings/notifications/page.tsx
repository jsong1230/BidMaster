/**
 * F-10 알림 시스템 — 알림 설정 페이지
 * /settings/notifications
 */
import Link from 'next/link';
import { NotificationSettingsForm } from '@/components/notifications/NotificationSettingsForm';

export default function NotificationSettingsPage() {
  return (
    <div className="p-6 max-w-screen-md mx-auto">
      {/* 페이지 헤더 */}
      <div className="mb-5">
        <div className="flex items-center gap-2 text-sm text-neutral-400 mb-2">
          <Link href="/settings/company" className="hover:text-neutral-600 transition-colors">
            설정
          </Link>
          <span>/</span>
          <span className="text-neutral-600">알림 설정</span>
        </div>
        <h1 className="text-xl font-bold text-neutral-800">알림 설정</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          알림 유형별 수신 채널을 설정합니다
        </p>
      </div>

      <NotificationSettingsForm />
    </div>
  );
}
