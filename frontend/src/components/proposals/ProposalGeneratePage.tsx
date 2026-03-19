/**
 * 제안서 생성 진행 페이지 컴포넌트
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useProposalStore } from '@/stores/proposalStore';
import { parseSSEEvent, type SSEEvent } from '@/lib/api/proposal';
import { GenerationProgress } from './GenerationProgress';
import { SectionProgressList } from './SectionProgressList';
import { toast } from '@/components/ui/Toast';

interface ProposalGeneratePageProps {
  proposalId: string;
}

export function ProposalGeneratePage({ proposalId }: ProposalGeneratePageProps) {
  const router = useRouter();
  const {
    generationProgress,
    connectGenerationStream,
    disconnectGenerationStream,
    updateGenerationProgress,
  } = useProposalStore();

  useEffect(() => {
    // SSE 스트리밍 연결
    connectGenerationStream(proposalId);

    // 이벤트 리스너 등록
    const eventSource = useProposalStore.getState().eventSource;
    if (!eventSource) return;

    eventSource.onmessage = (event) => {
      const parsed = parseSSEEvent(event.data);
      if (!parsed) return;

      handleSSEEvent(parsed);
    };

    eventSource.onerror = () => {
      toast.error('생성 중 연결이 끊어졌습니다. 다시 시도해주세요.');
      disconnectGenerationStream();
    };

    return () => {
      disconnectGenerationStream();
    };
  }, [proposalId]);

  const handleSSEEvent = (event: SSEEvent) => {
    switch (event.event) {
      case 'start':
        updateGenerationProgress((prev) => ({
          ...prev,
          proposalId: event.data.proposalId,
          totalSections: event.data.totalSections,
          sections: new Map(),
        }));
        break;

      case 'progress':
        updateGenerationProgress((prev) => {
          const sections = new Map(prev.sections);
          sections.set(event.data.sectionKey, { status: 'generating' });
          return {
            ...prev,
            currentSection: event.data.sectionKey,
            currentPercent: event.data.percent,
            sections,
          };
        });
        break;

      case 'section':
        updateGenerationProgress((prev) => {
          const sections = new Map(prev.sections);
          sections.set(event.data.sectionKey, {
            status: 'completed',
            content: event.data.content,
            wordCount: event.data.wordCount,
          });
          return {
            ...prev,
            completedSections: prev.completedSections + 1,
            sections,
          };
        });
        break;

      case 'complete':
        updateGenerationProgress((prev) => ({
          ...prev,
          isComplete: true,
          completedSections: event.data.totalSections,
        }));

        // 2초 후 상세 페이지로 이동
        setTimeout(() => {
          router.push(`/proposals/${proposalId}`);
          toast.success('제안서 생성이 완료되었습니다.');
        }, 2000);
        break;

      case 'error':
        updateGenerationProgress((prev) => ({
          ...prev,
          error: event.data,
        }));
        toast.error(event.data.message || '생성 중 오류가 발생했습니다.');
        break;
    }
  };

  const handleCancel = () => {
    if (confirm('생성을 취소하시겠습니까?')) {
      disconnectGenerationStream();
      router.push(`/proposals/${proposalId}`);
    }
  };

  // 에러 상태
  if (generationProgress?.error) {
    return (
      <div className="max-w-lg mx-auto text-center space-y-6">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-neutral-900 mb-2">생성 실패</h2>
          <p className="text-sm text-neutral-500 mb-4">
            {generationProgress.error.message || '제안서 생성 중 오류가 발생했습니다.'}
          </p>
          <button
            onClick={() => router.push(`/proposals/${proposalId}`)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 완료 상태
  if (generationProgress?.isComplete) {
    return (
      <div className="max-w-lg mx-auto text-center space-y-6">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-neutral-900 mb-2">제안서 생성 완료!</h2>
          <p className="text-sm text-neutral-500">
            총 {generationProgress.totalSections}개 섹션이 생성되었습니다.
          </p>
        </div>
        <p className="text-sm text-neutral-400">잠시 후 제안서 상세 페이지로 이동합니다...</p>
      </div>
    );
  }

  // 진행 중 상태
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* 헤더 */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-neutral-900 mb-2">제안서 생성 중...</h1>
        <p className="text-sm text-neutral-500">AI가 공고 정보를 분석하여 제안서를 작성하고 있습니다.</p>
      </div>

      {/* 프로그레스 */}
      <div className="bg-white border border-neutral-200 rounded-lg p-8">
        <GenerationProgress progress={generationProgress} />
      </div>

      {/* 섹션별 진행 상황 */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-neutral-900 mb-4">진행 상황</h3>
        <SectionProgressList progress={generationProgress} />
      </div>

      {/* 취소 버튼 */}
      <div className="text-center">
        <button
          onClick={handleCancel}
          className="text-sm text-neutral-500 hover:text-neutral-700 transition-colors"
        >
          생성 취소
        </button>
      </div>
    </div>
  );
}
