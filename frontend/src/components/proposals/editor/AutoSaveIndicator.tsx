/**
 * F-05 제안서 편집기 - 자동 저장 상태 표시 컴포넌트
 */

'use client';

import { useState, useEffect } from 'react';

interface AutoSaveIndicatorProps {
  /** 편집 중 여부 */
  isEditing?: boolean;
  /** 저장 콜백 */
  onSave?: () => Promise<void>;
  /** 마지막 저장 시간 */
  lastSavedAt?: Date | null;
}

type SaveStatus = 'saved' | 'editing' | 'saving' | 'error';

/**
 * 자동 저장 상태를 표시하는 인디케이터
 */
export function AutoSaveIndicator({
  isEditing = false,
  onSave,
  lastSavedAt: propLastSavedAt,
}: AutoSaveIndicatorProps) {
  const [status, setStatus] = useState<SaveStatus>('saved');
  const [internalLastSavedAt, setInternalLastSavedAt] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const lastSavedAt = propLastSavedAt || internalLastSavedAt;
  const lastSavedTimeAgo = getTimeAgo(lastSavedAt);

  useEffect(() => {
    if (isEditing) {
      setStatus('editing');
    }
  }, [isEditing]);

  const handleRetry = async () => {
    if (!onSave || isSaving || isRetrying) return;

    setIsRetrying(true);
    setIsSaving(true);
    setStatus('saving');

    try {
      await onSave();
      setInternalLastSavedAt(new Date());
      setStatus('saved');
    } catch (err) {
      setStatus('error');
    } finally {
      setIsSaving(false);
      setIsRetrying(false);
    }
  };

  const handleManualSave = async () => {
    if (!onSave || isSaving) return;

    setIsSaving(true);
    setStatus('saving');

    try {
      await onSave();
      setInternalLastSavedAt(new Date());
      setStatus('saved');
    } catch (err) {
      setStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const renderStatus = () => {
    switch (status) {
      case 'saved':
        return (
          <div className="flex items-center gap-2 text-success-700">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm">저장됨</span>
            {lastSavedTimeAgo && <span className="text-xs text-neutral-500">({lastSavedTimeAgo})</span>}
          </div>
        );

      case 'editing':
        return (
          <div className="flex items-center gap-2 text-neutral-600">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm">편집 중...</span>
          </div>
        );

      case 'saving':
        return (
          <div className="flex items-center gap-2 text-neutral-600">
            <div className="animate-spin">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <span className="text-sm">저장 중...</span>
          </div>
        );

      case 'error':
        return (
          <div className="flex items-center gap-2 text-error-700">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm">저장 실패</span>
            {onSave && (
              <button
                type="button"
                onClick={handleRetry}
                className="text-xs px-2 py-1 bg-error-100 text-error-700 rounded hover:bg-error-200 transition-colors"
              >
                재시도
              </button>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex items-center justify-between px-3 py-2 bg-neutral-50 border-b border-neutral-200">
      {renderStatus()}
      {onSave && status !== 'error' && (
        <button
          type="button"
          onClick={handleManualSave}
          disabled={isSaving}
          className="text-xs px-2 py-1 bg-white border border-neutral-300 rounded hover:bg-neutral-50 transition-colors disabled:opacity-50"
        >
          {isSaving ? '저장 중...' : '저장'}
        </button>
      )}
    </div>
  );
}

/**
 * 상대 시간 문자열 변환
 */
function getTimeAgo(date: Date | null): string {
  if (!date) return '';

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) {
    return '방금 전';
  } else if (diffMin < 60) {
    return `${diffMin}분 전`;
  } else if (diffHour < 24) {
    return `${diffHour}시간 전`;
  } else if (diffDay < 7) {
    return `${diffDay}일 전`;
  } else {
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
  }
}
