/**
 * F-05 제안서 편집기 - 평가 기준 패널 컴포넌트
 */

'use client';

import { useEvaluationProgress } from '../hooks/useEvaluationProgress';
import type { EvaluationChecklist } from '@/types/proposal';

interface EvaluationPanelProps {
  /** 체크리스트 */
  checklist?: EvaluationChecklist | null;
  /** 체크리스트 변경 콜백 */
  onChecklistChange?: (checklist: EvaluationChecklist) => void;
  /** 비활성화 여부 */
  disabled?: boolean;
}

const CheckCircleIcon = () => (
  <svg className="w-4 h-4 text-success-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const CircleIcon = () => (
  <svg className="w-4 h-4 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
  </svg>
);

/**
 * 평가 기준 체크리스트 패널
 */
export function EvaluationPanel({
  checklist: propChecklist,
  onChecklistChange,
  disabled = false,
}: EvaluationPanelProps) {
  const { checklist, achievementRate, toggleItem } = useEvaluationProgress({
    initialChecklist: propChecklist,
  });

  const handleToggle = (key: string) => {
    if (disabled || !onChecklistChange) return;

    const newChecklist = {
      ...checklist,
      [key]: {
        ...checklist[key],
        checked: !checklist[key]?.checked,
      },
    };

    toggleItem(key);
    onChecklistChange(newChecklist);
  };

  const getProgressColor = (rate: number): string => {
    if (rate >= 80) return 'bg-success-500';
    if (rate >= 60) return 'bg-secondary-500';
    if (rate >= 40) return 'bg-warning-500';
    return 'bg-error-500';
  };

  const checklistLabels: Record<string, string> = {
    technical_capability: '기술 역량',
    price_competitiveness: '가격 경쟁력',
    past_performance: '수행 실적',
    project_schedule: '프로젝트 일정',
    organization: '조직 구성',
  };

  return (
    <div className="space-y-4">
      {/* 달성률 */}
      <div className="bg-white border border-neutral-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-neutral-900">평가 기준 달성률</h3>
          <span className="text-lg font-bold text-neutral-900">{achievementRate}%</span>
        </div>
        <div className="w-full h-2 bg-neutral-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getProgressColor(achievementRate)}`}
            style={{ width: `${achievementRate}%` }}
          />
        </div>
      </div>

      {/* 체크리스트 */}
      <div className="bg-white border border-neutral-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-neutral-900 mb-3">평가 기준</h3>
        <div className="space-y-2">
          {Object.entries(checklist).map(([key, item]) => (
            <label
              key={key}
              className={`flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-neutral-50'
              }`}
            >
              <input
                type="checkbox"
                checked={item.checked}
                onChange={() => handleToggle(key)}
                disabled={disabled}
                className="mt-0.5 w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-neutral-900">
                    {checklistLabels[key] || key}
                  </span>
                  {item.checked ? <CheckCircleIcon /> : <CircleIcon />}
                </div>
                <span className="text-xs text-neutral-500">가중치: {item.weight}%</span>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
