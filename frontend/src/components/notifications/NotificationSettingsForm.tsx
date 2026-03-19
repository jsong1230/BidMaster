/**
 * F-10 알림 시스템 — 알림 설정 폼 컴포넌트
 * 알림 유형별 채널(이메일, 인앱) 토글
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import { useNotificationStore } from '@/lib/stores/notification-store';
import type { NotificationSetting, UpdateNotificationSettingItem } from '@/types/notification';

/** 토글 스위치 컴포넌트 */
function Toggle({
  checked,
  onChange,
  disabled,
  label,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex w-10 h-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#486581] focus:ring-offset-1 ${
        checked ? 'bg-[#486581]' : 'bg-neutral-200'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <span
        className={`inline-block w-4 h-4 bg-white rounded-full shadow-sm transition-transform mt-0.5 ${
          checked ? 'translate-x-5' : 'translate-x-0.5'
        }`}
      />
    </button>
  );
}

/** 스켈레톤 로딩 */
function SettingsSkeleton() {
  return (
    <div className="space-y-1">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex items-center justify-between p-4 border-b border-neutral-100 last:border-0">
          <div className="space-y-1.5">
            <div className="h-4 w-32 bg-neutral-200 rounded animate-pulse" />
            <div className="h-3 w-48 bg-neutral-200 rounded animate-pulse" />
          </div>
          <div className="flex gap-6">
            <div className="h-5 w-10 bg-neutral-200 rounded-full animate-pulse" />
            <div className="h-5 w-10 bg-neutral-200 rounded-full animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function NotificationSettingsForm() {
  const { settings, isSettingsLoading, error, fetchSettings, updateSettings } = useNotificationStore();

  // 로컬 편집 상태 (저장 전 임시)
  const [localSettings, setLocalSettings] = useState<NotificationSetting[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // 서버 데이터 반영
  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleToggle = useCallback(
    (notificationType: string, field: 'emailEnabled' | 'kakaoEnabled' | 'pushEnabled', value: boolean) => {
      setLocalSettings((prev) =>
        prev.map((s) =>
          s.notificationType === notificationType ? { ...s, [field]: value } : s
        )
      );
    },
    []
  );

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const payload: UpdateNotificationSettingItem[] = localSettings.map((s) => ({
        notificationType: s.notificationType,
        emailEnabled: s.emailEnabled,
        kakaoEnabled: s.kakaoEnabled,
        pushEnabled: s.pushEnabled,
      }));
      await updateSettings(payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } finally {
      setIsSaving(false);
    }
  }, [localSettings, updateSettings]);

  if (isSettingsLoading) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <SettingsSkeleton />
      </div>
    );
  }

  if (error && localSettings.length === 0) {
    return (
      <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">
        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        {error}
        <button
          onClick={() => fetchSettings()}
          className="ml-auto text-xs underline hover:no-underline"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* 헤더 설명 */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-neutral-500">
          알림 유형별로 수신 채널을 설정합니다.
        </p>
        <div className="flex items-center gap-6 text-xs font-medium text-neutral-400 pr-1">
          <span className="w-10 text-center">이메일</span>
          <span className="w-10 text-center">인앱</span>
        </div>
      </div>

      {/* 설정 목록 */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="divide-y divide-neutral-100">
          {localSettings.map((setting) => (
            <div key={setting.notificationType} className="flex items-center justify-between px-4 py-4">
              <div>
                <p className="text-sm font-medium text-neutral-800">{setting.label}</p>
                <p className="text-xs text-neutral-400 mt-0.5">
                  {setting.notificationType === 'bid_matched' && '적합도 70점 이상 공고 매칭 시 알림'}
                  {setting.notificationType === 'deadline' && '마감 D-3, D-1 시점에 알림'}
                  {setting.notificationType === 'bid_result' && '낙찰/실패 결과 등록 시 알림'}
                  {setting.notificationType === 'proposal_ready' && 'AI 제안서 생성 완료 시 알림'}
                </p>
              </div>
              <div className="flex items-center gap-6">
                <Toggle
                  checked={setting.emailEnabled}
                  onChange={(v) => handleToggle(setting.notificationType, 'emailEnabled', v)}
                  label={`${setting.label} 이메일 알림`}
                />
                <Toggle
                  checked={setting.pushEnabled}
                  onChange={(v) => handleToggle(setting.notificationType, 'pushEnabled', v)}
                  label={`${setting.label} 인앱 알림`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 저장 버튼 영역 */}
      <div className="flex items-center justify-end gap-3 mt-4">
        {saveSuccess && (
          <span className="flex items-center gap-1.5 text-sm text-green-600">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            저장되었습니다
          </span>
        )}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-4 py-2 text-sm font-medium bg-[#486581] text-white rounded-md hover:bg-[#334e68] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? '저장 중...' : '설정 저장'}
        </button>
      </div>
    </div>
  );
}
