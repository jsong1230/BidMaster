/**
 * 제안서 목록 페이지 컴포넌트
 */

'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { useProposalStore } from '@/stores/proposalStore';
import { ProposalCard } from './ProposalCard';

interface ProposalListPageProps {
  initialStatus?: string;
}

export function ProposalListPage({ initialStatus }: ProposalListPageProps) {
  const { proposals, isLoading, error, fetchProposals } = useProposalStore();
  const [filter, setFilter] = React.useState(initialStatus || '');

  useEffect(() => {
    fetchProposals(filter ? { status: filter as any } : undefined);
  }, [filter]);

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-neutral-900">제안서 관리</h1>
        <Link
          href="/proposals/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 제안서
        </Link>
      </div>

      {/* 상태 필터 */}
      <div className="flex gap-2">
        <FilterButton active={filter === ''} onClick={() => handleFilterChange('')}>
          전체
        </FilterButton>
        <FilterButton active={filter === 'generating'} onClick={() => handleFilterChange('generating')}>
          생성중
        </FilterButton>
        <FilterButton active={filter === 'ready'} onClick={() => handleFilterChange('ready')}>
          완료
        </FilterButton>
        <FilterButton active={filter === 'submitted'} onClick={() => handleFilterChange('submitted')}>
          제출완료
        </FilterButton>
      </div>

      {/* 에러 상태 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* 로딩 상태 */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* 빈 상태 */}
      {!isLoading && proposals.length === 0 && (
        <EmptyState onCreate={() => (window.location.href = '/proposals/new')} />
      )}

      {/* 제안서 목록 */}
      {!isLoading && proposals.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {proposals.map((proposal) => (
            <ProposalCard key={proposal.id} proposal={proposal} />
          ))}
        </div>
      )}
    </div>
  );
}

interface FilterButtonProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function FilterButton({ active, onClick, children }: FilterButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
        active
          ? 'bg-primary-100 text-primary-700'
          : 'bg-white border border-neutral-200 text-neutral-600 hover:bg-neutral-50'
      }`}
    >
      {children}
    </button>
  );
}

interface EmptyStateProps {
  onCreate: () => void;
}

function EmptyState({ onCreate }: EmptyStateProps) {
  return (
    <div className="text-center py-16">
      <div className="mx-auto w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-neutral-900 mb-2">제안서가 없습니다</h3>
      <p className="text-sm text-neutral-500 mb-4">
        첫 제안서를 생성하여 AI 도움을 받아보세요.
      </p>
      <button
        onClick={onCreate}
        className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        새 제안서 생성
      </button>
    </div>
  );
}
