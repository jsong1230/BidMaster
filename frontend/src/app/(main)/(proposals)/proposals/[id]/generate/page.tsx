/**
 * 제안서 생성 진행 페이지
 */

import { ProposalGeneratePage } from '@/components/proposals/ProposalGeneratePage';

interface GeneratePageProps {
  params: { id: string };
}

export default function GeneratePage({ params }: GeneratePageProps) {
  return <ProposalGeneratePage proposalId={params.id} />;
}
