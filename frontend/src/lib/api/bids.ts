/**
 * F-01 공고 자동 수집 및 매칭 — 공고 API 클라이언트
 * F-04 낙찰가 예측 및 투찰 전략 — strategy API 포함
 */
import { apiClient } from './client';
import type { BidDetail, BidItem, BidListParams, TriggerCollectionResponse } from '@/types/bid';
import type {
  BidMatchResult,
  MatchedBidItem,
  MatchedBidListParams,
} from '@/types/bid-match';
import type { StrategyResult, SimulationResult } from '@/types/strategy';
import type { PaginationMeta } from './client';

function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value));
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

export const bidsApi = {
  /**
   * 공고 목록 조회
   * GET /api/v1/bids
   */
  getBids: async (
    params?: BidListParams
  ): Promise<{ items: BidItem[]; meta: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
      status: params?.status,
      keyword: params?.keyword,
      region: params?.region,
      category: params?.category,
      bidType: params?.bidType,
      minBudget: params?.minBudget,
      maxBudget: params?.maxBudget,
      startDate: params?.startDate,
      endDate: params?.endDate,
      sortBy: params?.sortBy,
      sortOrder: params?.sortOrder,
    });
    const result = await apiClient.getList<BidItem>(`/bids${query}`);
    return {
      items: result.items,
      meta: result.meta ?? { page: 1, pageSize: 20, total: 0, totalPages: 0 },
    };
  },

  /**
   * 공고 상세 조회
   * GET /api/v1/bids/{id}
   */
  getBid: async (id: string): Promise<BidDetail> => {
    return apiClient.get<BidDetail>(`/bids/${id}`);
  },

  /**
   * 공고별 매칭 결과 조회
   * GET /api/v1/bids/{id}/matches
   */
  getBidMatches: async (bidId: string): Promise<BidMatchResult> => {
    return apiClient.get<BidMatchResult>(`/bids/${bidId}/matches`);
  },

  /**
   * 매칭 공고 목록 조회
   * GET /api/v1/bids/matched
   */
  getMatchedBids: async (
    params?: MatchedBidListParams
  ): Promise<{ items: MatchedBidItem[]; meta: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
      minScore: params?.minScore,
      recommendation: params?.recommendation !== 'all' ? params?.recommendation : undefined,
      sortBy: params?.sortBy,
      sortOrder: params?.sortOrder,
    });
    const result = await apiClient.getList<MatchedBidItem>(`/bids/matched${query}`);
    return {
      items: result.items,
      meta: result.meta ?? { page: 1, pageSize: 20, total: 0, totalPages: 0 },
    };
  },

  /**
   * 수동 수집 트리거 (관리자 전용)
   * POST /api/v1/bids/collect
   */
  triggerCollect: async (): Promise<TriggerCollectionResponse> => {
    return apiClient.post<TriggerCollectionResponse>('/bids/collect');
  },

  /**
   * 투찰 전략 분석 조회
   * GET /api/v1/bids/{id}/strategy
   */
  getBidStrategy: async (bidId: string): Promise<StrategyResult> => {
    return apiClient.get<StrategyResult>(`/bids/${bidId}/strategy`);
  },

  /**
   * 투찰가 시뮬레이션
   * POST /api/v1/bids/{id}/strategy/simulate
   */
  simulateBidStrategy: async (bidId: string, bidPrice: number): Promise<SimulationResult> => {
    return apiClient.post<SimulationResult>(`/bids/${bidId}/strategy/simulate`, { bidPrice });
  },
};
