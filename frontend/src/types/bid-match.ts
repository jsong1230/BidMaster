/**
 * F-01 공고 자동 수집 및 매칭 — 매칭 관련 TypeScript 타입 정의
 */

import type { PaginationMeta } from '@/lib/api/client';
import type { BidItem } from './bid';

export type RecommendationType = 'recommended' | 'neutral' | 'not_recommended';

/** 공고-사용자 매칭 결과 */
export interface BidMatchResult {
  id: string;
  bidId: string;
  userId: string;
  suitabilityScore: number;
  competitionScore: number;
  capabilityScore: number;
  marketScore: number;
  totalScore: number;
  recommendation: RecommendationType;
  recommendationReason?: string;
  isNotified: boolean;
  analyzedAt: string;
}

/** 매칭 공고 목록 아이템 */
export interface MatchedBidItem {
  id: string;
  bid: Pick<BidItem, 'id' | 'bidNumber' | 'title' | 'organization' | 'budget' | 'deadline' | 'status'>;
  totalScore: number;
  recommendation: RecommendationType;
  recommendationReason?: string;
  analyzedAt: string;
}

/** 매칭 공고 목록 응답 */
export interface MatchedBidListResponse {
  items: MatchedBidItem[];
  meta: PaginationMeta;
}

/** 매칭 공고 조회 파라미터 */
export interface MatchedBidListParams {
  page?: number;
  pageSize?: number;
  minScore?: number;
  recommendation?: RecommendationType | 'all';
  sortBy?: 'totalScore' | 'analyzedAt' | 'deadline';
  sortOrder?: 'asc' | 'desc';
}
