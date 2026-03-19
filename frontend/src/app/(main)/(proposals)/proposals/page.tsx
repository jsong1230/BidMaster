/**
 * 제안서 목록 페이지
 */

import { ProposalListPage } from '@/components/proposals/ProposalListPage';

export default function ProposalsPage({
  searchParams,
}: {
  searchParams: { status?: string };
}) {
  return <ProposalListPage initialStatus={searchParams.status} />;
}
