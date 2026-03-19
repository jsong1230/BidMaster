/**
 * 제안서 생성 페이지
 */

import { Suspense } from 'react';
import { ProposalCreatePage } from '@/components/proposals/ProposalCreatePage';

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    </div>
  );
}

export default function NewProposalPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <ProposalCreatePage />
    </Suspense>
  );
}
