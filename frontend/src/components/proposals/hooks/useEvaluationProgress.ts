/**
 * F-05 제안서 편집기 - 평가 기준 달성률 커스텀 훅
 */

import { useState, useCallback, useMemo } from 'react';
import type { EvaluationChecklist } from '@/types/proposal';

interface UseEvaluationProgressOptions {
  /** 초기 체크리스트 */
  initialChecklist?: EvaluationChecklist | null | Record<string, unknown>;
}

interface UseEvaluationProgressReturn {
  /** 현재 체크리스트 */
  checklist: Record<string, unknown>;
  /** 달성률 (0~100) */
  achievementRate: number;
  /** 체크리스트 업데이트 */
  updateChecklist: (newChecklist: Record<string, unknown>) => void;
  /** 개별 항목 토글 */
  toggleItem: (key: string) => void;
  /** 체크리스트 초기화 */
  resetChecklist: () => void;
}

/**
 * 평가 기준 체크리스트와 달성률 관리 훅
 */
export function useEvaluationProgress({
  initialChecklist,
}: UseEvaluationProgressOptions = {}): UseEvaluationProgressReturn {
  const [checklist, setChecklist] = useState<Record<string, unknown>>(initialChecklist || {});

  const achievementRate = useMemo(() => {
    const entries = Object.entries(checklist);
    if (entries.length === 0) return 0;

    let totalWeight = 0;
    let checkedWeight = 0;

    for (const [, item] of entries) {
      if (item && typeof item === 'object') {
        const weight = typeof item?.weight === 'number' ? item.weight : 0;
        totalWeight += weight;
        if (item?.checked) {
          checkedWeight += weight;
        }
      }
    }

    if (totalWeight === 0) return 0;
    return Math.round((checkedWeight / totalWeight) * 100);
  }, [checklist]);

  const updateChecklist = useCallback((newChecklist: Record<string, unknown>) => {
    setChecklist(newChecklist);
  }, []);

  const toggleItem = useCallback((key: string) => {
    setChecklist((prev) => {
      const item = prev[key];
      if (!item) return prev;

      return {
        ...prev,
        [key]: {
          ...item,
          checked: !(item as any).checked,
        },
      };
    });
  }, []);

  const resetChecklist = useCallback(() => {
    setChecklist((prev) => {
      const reset: Record<string, unknown> = {};
      for (const [key, item] of Object.entries(prev)) {
        if (item && typeof item === 'object') {
          reset[key] = {
            ...item,
            checked: false,
          };
        }
      }
      return reset;
    });
  }, []);

  return {
    checklist,
    achievementRate,
    updateChecklist,
    toggleItem,
    resetChecklist,
  };
}
