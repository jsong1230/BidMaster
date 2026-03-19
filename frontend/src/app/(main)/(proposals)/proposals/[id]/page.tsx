/**
 * 제안서 상세 페이지
 */

import { ProposalDetailPage } from '@/components/proposals/ProposalDetailPage';

interface DetailPageProps {
  params: { id: string };
}

export default function DetailPage({ params }: DetailPageProps) {
  return <ProposalDetailPage proposalId={params.id} />;
}
