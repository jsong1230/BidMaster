/**
 * 제안서 헤더 컴포넌트
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { ProposalDetail } from '@/types/proposal';
import { DownloadButton } from './DownloadButton';
import { toast } from '@/components/ui/Toast';

interface ProposalHeaderProps {
  proposal: ProposalDetail;
}

export function ProposalHeader({ proposal }: ProposalHeaderProps) {
  const router = useRouter();
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  const handleEdit = () => {
    // 편집 기능은 F-05에서 구현
    toast.info('편집 기능은 곧 지원됩니다.');
  };

  return (
    <div className="space-y-4">
      {/* 제목 및 상태 */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">{proposal.title}</h1>
        <div className="flex items-center gap-3 mt-2 text-sm text-neutral-500">
          <StatusBadge status={proposal.status} />
          <span>v{proposal.version}</span>
          <span>{proposal.pageCount}p</span>
          <span>{proposal.wordCount.toLocaleString()}자</span>
        </div>
      </div>

      {/* 액션 버튼 */}
      <div className="flex items-center gap-2">
        {/* 다운로드 드롭다운 */}
        <div className="relative">
          <button
            onClick={() => setShowDownloadMenu(!showDownloadMenu)}
            className="inline-flex items-center gap-2 px-4 py-2 border border-neutral-200 rounded-md text-sm font-medium text-neutral-700 hover:bg-neutral-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            다운로드
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showDownloadMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowDownloadMenu(false)}
              />
              <div className="absolute right-0 mt-2 w-48 bg-white border border-neutral-200 rounded-md shadow-lg z-20">
                <DownloadButton
                  proposalId={proposal.id}
                  format="docx"
                  label="Word (.docx)"
                  onComplete={() => setShowDownloadMenu(false)}
                />
                <DownloadButton
                  proposalId={proposal.id}
                  format="pdf"
                  label="PDF (.pdf)"
                  onComplete={() => setShowDownloadMenu(false)}
                />
              </div>
            </>
          )}
        </div>

        <button
          onClick={handleEdit}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          편집
        </button>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: ProposalDetail['status'] }) {
  switch (status) {
    case 'draft':
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-700">초안</span>;
    case 'generating':
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">생성중</span>;
    case 'ready':
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">완료</span>;
    case 'submitted':
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">제출완료</span>;
  }
}
