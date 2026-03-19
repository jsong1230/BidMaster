/**
 * 제안서 생성 페이지 컴포넌트
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useProposalStore } from '@/stores/proposalStore';
import { BidSelectModal } from './BidSelectModal';
import { SectionSelector } from './SectionSelector';
import { bidsApi } from '@/lib/api/bids';
import type { BidDetail } from '@/types/bid';
import { SECTION_LABELS, type SectionKey } from '@/types/proposal';
import { toast } from '@/components/ui/Toast';

const ALL_SECTIONS: SectionKey[] = ['overview', 'technical', 'methodology', 'schedule', 'organization', 'budget'];

export function ProposalCreatePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bidIdParam = searchParams.get('bidId');

  const { createProposal } = useProposalStore();

  const [isBidModalOpen, setIsBidModalOpen] = useState(false);
  const [selectedBid, setSelectedBid] = useState<BidDetail | null>(null);
  const [selectedSections, setSelectedSections] = useState<SectionKey[]>(ALL_SECTIONS);
  const [customInstructions, setCustomInstructions] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [bidLoading, setBidLoading] = useState(false);

  // URL 파라미터에서 bidId가 있으면 해당 공고 자동 로드
  useEffect(() => {
    if (bidIdParam) {
      loadBid(bidIdParam);
    }
  }, [bidIdParam]);

  const loadBid = async (id: string) => {
    setBidLoading(true);
    try {
      const bid = await bidsApi.getBid(id);
      setSelectedBid(bid);
    } catch (error) {
      console.error('공고 로딩 실패:', error);
      toast.error('공고를 불러오는데 실패했습니다.');
    } finally {
      setBidLoading(false);
    }
  };

  const handleBidSelect = (bidId: string) => {
    loadBid(bidId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedBid) {
      toast.error('공고를 선택해주세요.');
      return;
    }

    if (selectedSections.length === 0) {
      toast.error('최소 하나 이상의 섹션을 선택해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const proposal = await createProposal({
        bidId: selectedBid.id,
        sections: selectedSections,
        customInstructions: customInstructions.trim() || undefined,
      });

      toast.success('제안서 생성을 시작합니다.');
      router.push(`/proposals/${proposal.id}/generate`);
    } catch (error) {
      console.error('제안서 생성 실패:', error);
      toast.error(error instanceof Error ? error.message : '제안서 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (bidIdParam) {
      router.push('/bids');
    } else {
      router.push('/proposals');
    }
  };

  if (bidLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">제안서 생성</h1>
        <p className="text-sm text-neutral-500 mt-1">AI가 공고 정보를 바탕으로 제안서 초안을 생성합니다.</p>
      </div>

      {/* 폼 */}
      <form onSubmit={handleSubmit} className="bg-white border border-neutral-200 rounded-lg p-6 space-y-6">
        {/* 공고 선택 */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">공고</label>
          {selectedBid ? (
            <div className="p-4 bg-neutral-50 border border-neutral-200 rounded-md">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-neutral-900 mb-2">{selectedBid.title}</h3>
                  <div className="flex items-center gap-4 text-xs text-neutral-500">
                    <span>{selectedBid.organization}</span>
                    {selectedBid.budget && (
                      <span className="font-medium">{selectedBid.budget.toLocaleString()}원</span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setIsBidModalOpen(true)}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  변경
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setIsBidModalOpen(true)}
              className="w-full p-4 border-2 border-dashed border-neutral-300 rounded-md text-sm text-neutral-500 hover:border-primary-400 hover:text-primary-600 transition-colors"
            >
              공고 선택하기
            </button>
          )}
        </div>

        {/* 제목 (선택) */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">
            제안서 제목 (선택)
          </label>
          <input
            type="text"
            placeholder="입력하지 않으면 공고명 기반으로 자동 생성됩니다."
            className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <p className="text-xs text-neutral-500 mt-1">
            빈 값으로 두면 공고명에서 자동 생성됩니다.
          </p>
        </div>

        {/* 섹션 선택 */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">생성할 섹션</label>
          <SectionSelector selected={selectedSections} onChange={setSelectedSections} />
        </div>

        {/* 추가 지시사항 */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">
            추가 지시사항 (선택)
          </label>
          <textarea
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="특별히 강조하고 싶은 내용이나 포함하길 원하는 항목을 입력하세요."
            rows={4}
            className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
        </div>

        {/* 버튼 */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-200">
          <button
            type="button"
            onClick={handleCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-neutral-200 rounded-md text-sm font-medium text-neutral-600 hover:bg-neutral-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isLoading || !selectedBid || selectedSections.length === 0}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '생성 중...' : '제안서 생성하기'}
          </button>
        </div>
      </form>

      {/* 공고 선택 모달 */}
      <BidSelectModal
        isOpen={isBidModalOpen}
        onClose={() => setIsBidModalOpen(false)}
        onSelect={handleBidSelect}
      />
    </div>
  );
}
