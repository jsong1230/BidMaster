/**
 * F-03 제안서 AI 초안 생성 — 제안서 관련 TypeScript 타입 정의
 */

import type { PaginationMeta } from '@/lib/api/client';

// ========== 상태 타입 ==========

/** 제안서 상태 */
export type ProposalStatus = 'draft' | 'generating' | 'ready' | 'submitted';

/** 섹션 키 */
export type SectionKey = 'overview' | 'technical' | 'methodology' | 'schedule' | 'organization' | 'budget';

/** 섹션 라벨 */
export const SECTION_LABELS: Record<SectionKey, string> = {
  overview: '사업 개요',
  technical: '기술 제안',
  methodology: '수행 방법론',
  schedule: '추진 일정',
  organization: '조직 구성',
  budget: '예산',
};

// ========== 제안서 (Proposal) ==========

/** 제안서 목록 아이템 */
export interface Proposal {
  id: string;
  bidId: string;
  bidTitle: string | null;
  title: string;
  status: ProposalStatus;
  version: number;
  pageCount: number;
  wordCount: number;
  createdAt: string;
  updatedAt: string;
}

/** 제안서 상세 */
export interface ProposalDetail extends Proposal {
  companyId: string;
  evaluationChecklist: Record<string, unknown>;
  sections: ProposalSection[];
  generatedAt: string | null;
}

/** 제안서 섹션 */
export interface ProposalSection {
  id: string;
  sectionKey: SectionKey;
  title: string;
  order: number;
  content: string | null;
  wordCount: number;
  isAiGenerated: boolean;
  metadata: Record<string, unknown>;
  updatedAt: string;
}

// ========== 제안서 목록 ==========

/** 제안서 목록 응답 */
export interface ProposalListResponse {
  items: Proposal[];
  meta?: PaginationMeta;
}

/** 제안서 목록 조회 파라미터 */
export interface ProposalListParams {
  page?: number;
  pageSize?: number;
  status?: ProposalStatus | '';
  bidId?: string;
  sortBy?: 'createdAt' | 'updatedAt';
  sortOrder?: 'asc' | 'desc';
}

// ========== 제안서 생성 ==========

/** 제안서 생성 요청 */
export interface CreateProposalRequest {
  bidId: string;
  title?: string;
  sections?: SectionKey[];
  customInstructions?: string;
}

/** 제안서 생성 응답 */
export interface CreateProposalResponse {
  id: string;
  bidId: string;
  title: string;
  status: ProposalStatus;
  sections: SectionKey[];
  createdAt: string;
}

// ========== SSE 이벤트 ==========

/** SSE 이벤트 데이터 공통 */
export interface SSEEventData {
  [key: string]: unknown;
}

/** SSE 이벤트 타입 */
export type SSEEventType = 'start' | 'progress' | 'section' | 'complete' | 'error';

/** SSE 이벤트 시작 */
export interface SSEStartData extends SSEEventData {
  proposalId: string;
  totalSections: number;
  message: string;
}

/** SSE 이벤트 진행 상황 */
export interface SSEProgressData extends SSEEventData {
  sectionKey: SectionKey;
  percent: number;
  message: string;
}

/** SSE 이벤트 섹션 완료 */
export interface SSESectionData extends SSEEventData {
  sectionKey: SectionKey;
  title: string;
  content: string;
  wordCount: number;
  order: number;
}

/** SSE 이벤트 전체 완료 */
export interface SSECompleteData extends SSEEventData {
  proposalId: string;
  totalSections: number;
  totalWordCount: number;
  generatedAt: string;
}

/** SSE 이벤트 에러 */
export interface SSEErrorData extends SSEEventData {
  code: string;
  message: string;
}

/** SSE 이벤트 */
export type SSEEvent =
  | { event: 'start'; data: SSEStartData }
  | { event: 'progress'; data: SSEProgressData }
  | { event: 'section'; data: SSESectionData }
  | { event: 'complete'; data: SSECompleteData }
  | { event: 'error'; data: SSEErrorData };

/** 생성 진행 상태 */
export interface GenerationProgress {
  proposalId: string;
  totalSections: number;
  completedSections: number;
  currentSection: SectionKey | null;
  currentPercent: number;
  sections: Map<SectionKey, { status: 'pending' | 'generating' | 'completed'; content?: string; wordCount?: number }>;
  error: SSEErrorData | null;
  isComplete: boolean;
}

// ========== 섹션 재생성 ==========

/** 섹션 재생성 요청 */
export interface RegenerateSectionRequest {
  customInstructions?: string;
}

/** 섹션 재생성 응답 */
export interface RegenerateSectionResponse {
  sectionKey: SectionKey;
  title: string;
  content: string;
  wordCount: number;
  isAiGenerated: boolean;
  updatedAt: string;
}

// ========== 다운로드 ==========

/** 다운로드 형식 */
export type DownloadFormat = 'docx' | 'pdf';

/** 다운로드 응답 */
export interface DownloadResponse {
  filename: string;
  contentType: string;
  data: Blob;
}

// ========== F-05 제안서 편집기 ==========

/** 평가 기준 체크리스트 항목 */
export interface ChecklistItem {
  checked: boolean;
  weight: number;
  [key: string]: unknown;
}

/** 평가 기준 체크리스트 */
export interface EvaluationChecklist {
  [key: string]: ChecklistItem;
}

/** 자동 저장 요청 */
export interface AutoSaveRequest {
  sections: Array<{
    sectionKey: string;
    content: string;
    wordCount: number;
  }>;
}

/** 자동 저장 응답 */
export interface AutoSaveResponse {
  savedAt: string;
  wordCount: number;
}

/** 검증 경고 */
export interface ValidationWarning {
  type: 'required_field' | 'page_limit' | 'checklist_incomplete';
  section?: string;
  current?: number;
  limit?: number;
  message: string;
}

/** 섹션 통계 */
export interface SectionStats {
  sectionKey: string;
  wordCount: number;
  isEmpty: boolean;
}

/** 검증 응답 */
export interface ValidationResponse {
  isValid: boolean;
  warnings: ValidationWarning[];
  stats: {
    totalWordCount: number;
    estimatedPages: number;
    sectionStats: SectionStats[];
  };
}

/** 평가 기준 체크리스트 업데이트 요청 */
export interface ChecklistUpdateRequest {
  checklist: EvaluationChecklist;
}

/** 평가 기준 체크리스트 업데이트 응답 */
export interface ChecklistUpdateResponse {
  checklist: EvaluationChecklist;
  achievementRate: number;
  updatedAt: string;
}
