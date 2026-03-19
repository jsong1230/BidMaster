/**
 * F-06 입찰 현황 대시보드 타입 정의
 */

/** 마감 임박 공고 */
export interface UpcomingDeadline {
  bidId: string;
  title: string;
  deadline: string;
  daysLeft: number;
  trackingStatus: TrackingStatusType;
}

/** 대시보드 KPI 요약 */
export interface DashboardSummary {
  period: string;
  participationCount: number;
  submissionCount: number;
  wonCount: number;
  lostCount: number;
  pendingCount: number;
  totalWonAmount: number;
  winRate: number;
  averageWonAmount: number;
  roi: number;
  upcomingDeadlines: UpcomingDeadline[];
}

/** 파이프라인 아이템 */
export interface PipelineItem {
  trackingId: string;
  bidId: string;
  title: string;
  organization: string;
  budget: number;
  deadline: string;
  daysLeft: number;
  totalScore: number | null;
  updatedAt: string;
  myBidPrice?: number | null;
}

/** 파이프라인 단계 */
export interface PipelineStage {
  status: TrackingStatusType;
  label: string;
  count: number;
  items: PipelineItem[];
}

/** 파이프라인 전체 데이터 */
export interface PipelineData {
  stages: PipelineStage[];
}

/** 월별 통계 */
export interface MonthlyStat {
  month: string;
  participationCount: number;
  submissionCount: number;
  wonCount: number;
  lostCount: number;
  winRate: number;
  totalWonAmount: number;
  averageBidRate: number;
}

/** 누적 통계 */
export interface CumulativeStat {
  totalParticipation: number;
  totalSubmission: number;
  totalWon: number;
  totalLost: number;
  overallWinRate: number;
  totalWonAmount: number;
  averageWonAmount: number;
  overallRoi: number;
}

/** 통계 데이터 */
export interface StatisticsData {
  monthly: MonthlyStat[];
  cumulative: CumulativeStat;
}

/** 추적 상태 타입 */
export type TrackingStatusType = 'interested' | 'participating' | 'submitted' | 'won' | 'lost';

/** 추적 상태 응답 */
export interface TrackingResponse {
  id: string;
  bidId: string;
  userId: string;
  status: TrackingStatusType;
  myBidPrice: number | null;
  isWinner: boolean | null;
  submittedAt: string | null;
  resultAt: string | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
}

/** 추적 상태 Upsert 요청 */
export interface TrackingUpsertRequest {
  status: TrackingStatusType;
  myBidPrice?: number;
  notes?: string;
}

/** 낙찰 이력 아이템 */
export interface WinHistoryItem {
  id: string;
  bidId: string;
  userId: string;
  status: TrackingStatusType;
  myBidPrice: number | null;
  isWinner: boolean;
  submittedAt: string | null;
  resultAt: string | null;
  /** 공고 정보 (조인) */
  title?: string;
  organization?: string;
  budget?: number;
  bidRate?: number;
}

/** 낙찰 이력 응답 */
export interface WinHistoryResponse {
  items: WinHistoryItem[];
}

/** 낙찰 이력 조회 파라미터 */
export interface WinHistoryParams {
  page?: number;
  pageSize?: number;
  startDate?: string;
  endDate?: string;
  sortBy?: 'resultAt' | 'myBidPrice';
  sortOrder?: 'asc' | 'desc';
}
