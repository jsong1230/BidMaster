/**
 * 제안서 상세 페이지 컴포넌트
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useProposalStore } from '@/stores/proposalStore';
import { useEditorStore } from '@/stores/editorStore';
import { ProposalHeader } from './ProposalHeader';
import { SectionNavigator } from './sidebar/SectionNavigator';
import { EvaluationPanel } from './sidebar/EvaluationPanel';
import { SectionEditor } from './editor/SectionEditor';
import type { SectionKey } from '@/types/proposal';

interface ProposalDetailPageProps {
  proposalId: string;
}

export function ProposalDetailPage({ proposalId }: ProposalDetailPageProps) {
  const router = useRouter();
  const { currentProposal, isDetailLoading, detailError, fetchProposal, resetDetail } = useProposalStore();
  const { mode, setActiveSection, reset: resetEditor } = useEditorStore();
  const [checklist, setChecklist] = useState<Record<string, unknown> | null>(null);

  // 편집 모드 vs 뷰 모드 결정 (ready 상태만 편집 가능)
  const canEdit = currentProposal?.status === 'ready' || currentProposal?.status === 'draft';

  useEffect(() => {
    fetchProposal(proposalId);

    return () => {
      resetDetail();
      resetEditor();
    };
  }, [proposalId, resetEditor]);

  // 생성 중 상태면 진행 페이지로 리다이렉트
  useEffect(() => {
    if (currentProposal?.status === 'generating') {
      router.push(`/proposals/${proposalId}/generate`);
    }
  }, [currentProposal?.status, proposalId, router]);

  // 평가 체크리스트 초기화
  useEffect(() => {
    if (currentProposal?.evaluationChecklist) {
      setChecklist(currentProposal.evaluationChecklist);
    }
  }, [currentProposal?.evaluationChecklist]);

  // 평가 체크리스트 업데이트 핸들러
  const handleChecklistChange = async (newChecklist: Record<string, unknown>) => {
    setChecklist(newChecklist);
    try {
      await import('@/lib/api/proposal').then(({ proposalApi }) => {
        return proposalApi.updateEvaluationChecklist(proposalId, { checklist: newChecklist as any });
      });
    } catch (err) {
      console.error('평가 체크리스트 업데이트 실패:', err);
    }
  };

  if (isDetailLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (detailError) {
    return (
      <div className="max-w-lg mx-auto text-center space-y-4">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-neutral-900 mb-2">오류 발생</h2>
          <p className="text-sm text-neutral-500">{detailError}</p>
        </div>
        <button
          onClick={() => router.push('/proposals')}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  if (!currentProposal) {
    return null;
  }

  const sortedSections = [...currentProposal.sections].sort((a, b) => a.order - b.order);
  const sectionNavigatorItems = sortedSections.map((s) => ({
    key: s.sectionKey,
    title: s.title,
    completed: s.wordCount > 0,
  }));

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* 헤더 */}
      <ProposalHeader proposal={currentProposal} />

      {/* 메인 콘텐츠 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 사이드바 (데스크톱) */}
        <aside className="hidden lg:block space-y-4 sticky top-6 h-fit">
          {/* 섹션 네비게이션 */}
          <div className="bg-white border border-neutral-200 rounded-lg p-4">
            <SectionNavigator
              sections={sectionNavigatorItems}
              activeSection={currentProposal.sections.find((s) => s.wordCount > 0)?.sectionKey}
              onSectionClick={(key) => setActiveSection(key as SectionKey)}
            />
          </div>

          {/* 평가 기준 패널 */}
          {checklist && (
            <EvaluationPanel
              checklist={checklist as any}
              onChecklistChange={handleChecklistChange}
              disabled={!canEdit}
            />
          )}
        </aside>

        {/* 섹션 내용 */}
        <div className="lg:col-span-3 space-y-8">
          {sortedSections.map((section) => (
            <SectionEditor
              key={section.id}
              section={section}
              proposalId={proposalId}
              mode={canEdit ? 'edit' : 'view'}
              sectionId={`section-${section.sectionKey}`}
            />
          ))}
        </div>
      </div>

      {/* 모바일 사이드바 */}
      <div className="lg:hidden fixed bottom-4 left-4 right-4 z-40">
        <div className="bg-white border border-neutral-200 rounded-lg shadow-lg p-4 max-h-48 overflow-y-auto">
          <SectionNavigator
            sections={sectionNavigatorItems}
            activeSection={currentProposal.sections.find((s) => s.wordCount > 0)?.sectionKey}
            onSectionClick={(key) => setActiveSection(key as SectionKey)}
          />
        </div>
      </div>
    </div>
  );
}
