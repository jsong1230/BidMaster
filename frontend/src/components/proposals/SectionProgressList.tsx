/**
 * 섹션별 진행 상황 목록 컴포넌트
 */

'use client';

import { GenerationProgress, SECTION_LABELS, type SectionKey } from '@/types/proposal';

interface SectionProgressListProps {
  progress: GenerationProgress | null;
}

export function SectionProgressList({ progress }: SectionProgressListProps) {
  if (!progress) return null;

  const ALL_SECTIONS: SectionKey[] = ['overview', 'technical', 'methodology', 'schedule', 'organization', 'budget'];

  return (
    <div className="space-y-2">
      {ALL_SECTIONS.map((sectionKey) => {
        const sectionState = progress.sections.get(sectionKey);
        const isCompleted = sectionState?.status === 'completed';
        const isGenerating = sectionState?.status === 'generating';
        const isPending = sectionState?.status === 'pending';

        return (
          <div
            key={sectionKey}
            className={`flex items-center gap-3 p-3 rounded-md border ${
              isCompleted
                ? 'border-green-200 bg-green-50'
                : isGenerating
                ? 'border-blue-200 bg-blue-50'
                : 'border-neutral-200 bg-white'
            }`}
          >
            {/* 상태 아이콘 */}
            {isCompleted ? (
              <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : isGenerating ? (
              <div className="w-5 h-5 flex-shrink-0">
                <svg className="animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            ) : (
              <svg className="w-5 h-5 text-neutral-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}

            {/* 섹션명 */}
            <span className={`flex-1 text-sm ${isCompleted ? 'text-neutral-700' : isGenerating ? 'text-blue-700 font-medium' : 'text-neutral-500'}`}>
              {SECTION_LABELS[sectionKey]}
            </span>

            {/* 상태 텍스트 */}
            {isCompleted && sectionState?.wordCount && (
              <span className="text-xs text-neutral-500">({sectionState.wordCount}자)</span>
            )}
            {isGenerating && <span className="text-xs text-blue-600">생성 중...</span>}
            {isPending && <span className="text-xs text-neutral-400">대기 중</span>}
          </div>
        );
      })}
    </div>
  );
}
