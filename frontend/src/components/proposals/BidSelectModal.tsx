/**
 * 공고 선택 모달 컴포넌트
 */

'use client';

import { useState, useEffect } from 'react';
import { bidsApi } from '@/lib/api/bids';
import type { BidItem } from '@/types/bid';
import { BidStatusBadge } from '@/components/bids/BidStatusBadge';
import { DeadlineBadge } from '@/components/bids/DeadlineBadge';

interface BidSelectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (bidId: string) => void;
}

function formatBudget(budget?: number): string {
  if (!budget) return '-';
  if (budget >= 100_000_000) {
    return `${(budget / 100_000_000).toFixed(0)}억원`;
  }
  if (budget >= 10_000) {
    return `${(budget / 10_000).toFixed(0)}만원`;
  }
  return `${budget.toLocaleString()}원`;
}

export function BidSelectModal({ isOpen, onClose, onSelect }: BidSelectModalProps) {
  const [bids, setBids] = useState<BidItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadBids();
    }
  }, [isOpen]);

  const loadBids = async () => {
    setLoading(true);
    try {
      const result = await bidsApi.getBids({ status: 'open', pageSize: 50 });
      setBids(result.items);
    } catch (error) {
      console.error('공고 목록 로딩 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredBids = bids.filter(
    (bid) =>
      bid.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      bid.organization.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelect = (bidId: string) => {
    onSelect(bidId);
    onClose();
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
      <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col m-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200">
          <h2 className="text-lg font-semibold text-neutral-900">공고 선택</h2>
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

        {/* 검색 */}
        <div className="p-4 border-b border-neutral-200">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="공고명 또는 기관명으로 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* 공고 목록 */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            </div>
          ) : filteredBids.length === 0 ? (
            <div className="text-center py-8 text-sm text-neutral-500">
              검색 결과가 없습니다.
            </div>
          ) : (
            <div className="space-y-2">
              {filteredBids.map((bid) => (
                <button
                  key={bid.id}
                  onClick={() => handleSelect(bid.id)}
                  className="w-full text-left p-4 border border-neutral-200 rounded-md hover:border-primary-300 hover:bg-primary-50 transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <BidStatusBadge status={bid.status} />
                        <DeadlineBadge deadline={bid.deadline} />
                      </div>
                      <h3 className="text-sm font-semibold text-neutral-900 mb-1 line-clamp-2">
                        {bid.title}
                      </h3>
                      <div className="flex items-center gap-4 text-xs text-neutral-500">
                        <span>{bid.organization}</span>
                        <span className="font-medium">{formatBudget(bid.budget)}</span>
                      </div>
                    </div>
                    <svg className="w-5 h-5 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 푸터 */}
        <div className="p-4 border-t border-neutral-200 bg-neutral-50 rounded-b-lg">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 border border-neutral-200 rounded-md text-sm font-medium text-neutral-600 hover:bg-white transition-colors"
          >
            취소
          </button>
        </div>
      </div>
    </div>
  );
}
