/**
 * F-01 공고 자동 수집 및 매칭 — 공고 관련 TypeScript 타입 정의
 */

import type { PaginationMeta } from '@/lib/api/client';

export type BidStatus = 'open' | 'closed' | 'awarded' | 'cancelled';

// ========== Bid (공고) ==========

/** 공고 목록 아이템 */
export interface BidItem {
  id: string;
  bidNumber: string;
  title: string;
  organization: string;
  region?: string;
  category?: string;
  bidType?: string;
  contractMethod?: string;
  budget?: number;
  announcementDate?: string;
  deadline: string;
  status: BidStatus;
  attachmentCount?: number;
  crawledAt?: string;
}

/** 공고 첨부파일 */
export interface BidAttachment {
  id: string;
  filename: string;
  fileType: string;
  fileUrl: string;
  hasExtractedText: boolean;
}

/** 평가 기준 */
export interface ScoringCriteria {
  technical?: number;
  price?: number;
}

/** 공고 상세 */
export interface BidDetail extends BidItem {
  description?: string;
  estimatedPrice?: number;
  openDate?: string;
  scoringCriteria?: ScoringCriteria;
  attachments: BidAttachment[];
  createdAt: string;
}

/** 공고 목록 응답 */
export interface BidListResponse {
  items: BidItem[];
  meta: PaginationMeta;
}

/** 공고 목록 조회 파라미터 */
export interface BidListParams {
  page?: number;
  pageSize?: number;
  status?: BidStatus | '';
  keyword?: string;
  region?: string;
  category?: string;
  bidType?: string;
  minBudget?: number;
  maxBudget?: number;
  startDate?: string;
  endDate?: string;
  sortBy?: 'deadline' | 'announcementDate' | 'budget' | 'createdAt';
  sortOrder?: 'asc' | 'desc';
}

// ========== 공고 수집 트리거 ==========

export interface TriggerCollectionResponse {
  message: string;
  triggeredAt: string;
}
