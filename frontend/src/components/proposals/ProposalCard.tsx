/**
 * 제안서 카드 컴포넌트
 */

import Link from 'next/link';
import type { Proposal } from '@/types/proposal';
import { SECTION_LABELS, type SectionKey } from '@/types/proposal';

interface ProposalCardProps {
  proposal: Proposal;
}

function getStatusInfo(status: Proposal['status']) {
  switch (status) {
    case 'draft':
      return { label: '초안', color: 'bg-neutral-100 text-neutral-700' };
    case 'generating':
      return { label: '생성중', color: 'bg-blue-100 text-blue-700' };
    case 'ready':
      return { label: '완료', color: 'bg-green-100 text-green-700' };
    case 'submitted':
      return { label: '제출완료', color: 'bg-purple-100 text-purple-700' };
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

export function ProposalCard({ proposal }: ProposalCardProps) {
  const statusInfo = getStatusInfo(proposal.status);

  return (
    <Link href={`/proposals/${proposal.id}`}>
      <div className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
        {/* 상태 배지 */}
        <div className="flex items-center gap-2 mb-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusInfo.color}`}>
            {statusInfo.label}
          </span>
          {proposal.version > 1 && (
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-600">
              v{proposal.version}
            </span>
          )}
        </div>

        {/* 제목 */}
        <h3 className="text-sm font-semibold text-neutral-800 mb-2 line-clamp-2 leading-snug">
          {proposal.title}
        </h3>

        {/* 메타 정보 */}
        <div className="space-y-1 text-xs text-neutral-500">
          {proposal.bidTitle && (
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span className="line-clamp-1">{proposal.bidTitle}</span>
            </div>
          )}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{proposal.wordCount.toLocaleString()}자</span>
            </div>
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{formatDate(proposal.createdAt)}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
