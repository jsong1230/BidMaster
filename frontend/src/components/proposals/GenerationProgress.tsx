/**
 * 생성 진행 상황 컴포넌트
 */

'use client';

import type { GenerationProgress } from '@/types/proposal';

interface GenerationProgressProps {
  progress: GenerationProgress | null;
}

export function GenerationProgress({ progress }: GenerationProgressProps) {
  if (!progress) return null;

  const percent = Math.round((progress.completedSections / progress.totalSections) * 100);

  return (
    <div className="text-center space-y-6">
      {/* 프로그레스 바 */}
      <div className="w-full bg-neutral-200 rounded-full h-4 overflow-hidden">
        <div
          className="h-full bg-primary-600 transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* 진행률 텍스트 */}
      <div>
        <p className="text-2xl font-bold text-neutral-900">{percent}%</p>
        <p className="text-sm text-neutral-500 mt-1">
          {progress.completedSections} / {progress.totalSections} 섹션 완료
        </p>
      </div>

      {/* 메시지 */}
      {progress.currentSection && (
        <p className="text-sm text-primary-600">
          {SECTION_LABELS[progress.currentSection]} 섹션 생성 중...
        </p>
      )}
    </div>
  );
}

const SECTION_LABELS: Record<string, string> = {
  overview: '사업 개요',
  technical: '기술 제안',
  methodology: '수행 방법론',
  schedule: '추진 일정',
  organization: '조직 구성',
  budget: '예산',
};
