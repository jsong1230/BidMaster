/**
 * 섹션 재생성 모달 컴포넌트
 */

'use client';

import { useState } from 'react';
import { useProposalStore } from '@/stores/proposalStore';
import type { SectionKey } from '@/types/proposal';
import { toast } from '@/components/ui/Toast';

interface RegenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
  proposalId: string;
  sectionKey: SectionKey;
  sectionTitle: string;
  onComplete?: (updatedSection: any) => void;
}

export function RegenerateModal({
  isOpen,
  onClose,
  proposalId,
  sectionKey,
  sectionTitle,
  onComplete,
}: RegenerateModalProps) {
  const { regenerateSection } = useProposalStore();
  const [instructions, setInstructions] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsLoading(true);
    try {
      await regenerateSection(proposalId, sectionKey, {
        customInstructions: instructions.trim() || undefined,
      });
      toast.success('섹션이 재생성되었습니다.');
      onComplete?.({});
      onClose();
    } catch (error) {
      console.error('재생성 실패:', error);
      toast.error(error instanceof Error ? error.message : '재생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 오버레이 */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 모달 */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full m-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200">
          <h2 className="text-lg font-semibold text-neutral-900">섹션 재생성</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-neutral-100 rounded-md transition-colors"
            aria-label="닫기"
          >
            <svg className="w-5 h-5 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 본문 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* 대상 섹션 */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">대상 섹션</label>
            <div className="p-3 bg-neutral-50 border border-neutral-200 rounded-md text-sm text-neutral-700">
              {sectionTitle}
            </div>
          </div>

          {/* 추가 지시사항 */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              추가 지시사항 (선택)
            </label>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="예: 더 구체적인 수행 방법론을 포함해주세요, Agile 방법론을 강조해주세요..."
              rows={4}
              className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
            <p className="text-xs text-neutral-500 mt-1">
              이전 내용을 바탕으로 재작성합니다. 특별히 강조하고 싶은 내용을 입력하세요.
            </p>
          </div>

          {/* 버튼 */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 border border-neutral-200 rounded-md text-sm font-medium text-neutral-600 hover:bg-neutral-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '재생성 중...' : '재생성하기'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
