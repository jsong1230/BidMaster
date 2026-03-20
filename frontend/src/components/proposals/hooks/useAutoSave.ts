/**
 * F-05 제안서 편집기 - 자동 저장 커스텀 훅
 */

import { useEffect, useRef, useCallback, useState } from 'react';

interface UseAutoSaveOptions {
  /** 디바운스 시간 (ms) */
  debounceMs?: number;
  /** 저장 콜백 */
  onSave?: () => Promise<void>;
  /** 컴포넌트 언마운트 시 강제 저장 여부 */
  saveOnUnmount?: boolean;
}

export interface AutoSaveReturn {
  /** 저장 트리거 함수 */
  triggerSave: () => void;
  /** 저장 중 여부 */
  isSaving: boolean;
  /** 에러 메시지 */
  error: string | null;
  /** 마지막 저장 시간 */
  lastSavedAt: Date | null;
}

/**
 * 자동 저장 훅
 * 30초 디바운스 후 자동 저장
 */
export function useAutoSave({
  debounceMs = 30000,
  onSave,
  saveOnUnmount = true,
}: UseAutoSaveOptions = {}): AutoSaveReturn {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingSaveRef = useRef(false);

  const triggerSave = useCallback(() => {
    pendingSaveRef.current = true;

    // 기존 타이머 취소
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // 새 타이머 설정
    timeoutRef.current = setTimeout(async () => {
      if (!pendingSaveRef.current || !onSave || isSaving) {
        return;
      }

      setIsSaving(true);
      setError(null);
      pendingSaveRef.current = false;

      try {
        await onSave();
        setLastSavedAt(new Date());
      } catch (err) {
        setError(err instanceof Error ? err.message : '저장에 실패했습니다.');
      } finally {
        setIsSaving(false);
      }
    }, debounceMs);
  }, [debounceMs, onSave, isSaving]);

  // 컴포넌트 언마운트 시 강제 저장
  useEffect(() => {
    return () => {
      // 타이머 취소
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // pending 저장이 있으면 즉시 저장
      if (saveOnUnmount && pendingSaveRef.current && onSave && !isSaving) {
        onSave().catch(() => {
          // 언마운트 시 에러는 무시
        });
      }
    };
  }, [saveOnUnmount, onSave, isSaving]);

  // Ctrl+S 단축키로 수동 저장
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();

        // 기존 타이머 취소 후 즉시 저장
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        if (onSave && !isSaving) {
          setIsSaving(true);
          setError(null);
          pendingSaveRef.current = false;

          onSave()
            .then(() => {
              setLastSavedAt(new Date());
            })
            .catch((err) => {
              setError(err instanceof Error ? err.message : '저장에 실패했습니다.');
            })
            .finally(() => {
              setIsSaving(false);
            });
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSave, isSaving]);

  return {
    triggerSave,
    isSaving,
    error,
    lastSavedAt,
  };
}
