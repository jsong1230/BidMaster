/**
 * F-06 입찰 현황 대시보드 — API 클라이언트
 */
import { apiClient } from './client';
import type { PaginationMeta } from './client';
import type {
  DashboardSummary,
  PipelineData,
  StatisticsData,
  TrackingResponse,
  TrackingUpsertRequest,
  WinHistoryItem,
  WinHistoryParams,
} from '@/types/dashboard';

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

export const dashboardApi = {
  /**
   * 대시보드 KPI 요약 조회
   * GET /api/v1/dashboard/summary?period=current_month
   */
  getDashboardSummary: async (period = 'current_month'): Promise<DashboardSummary> => {
    return apiClient.get<DashboardSummary>(`/dashboard/summary?period=${period}`);
  },

  /**
   * 파이프라인 단계별 현황 조회
   * GET /api/v1/dashboard/pipeline
   */
  getDashboardPipeline: async (): Promise<PipelineData> => {
    return apiClient.get<PipelineData>('/dashboard/pipeline');
  },

  /**
   * 성과 통계 (월별 트렌드) 조회
   * GET /api/v1/dashboard/statistics?months=6
   */
  getDashboardStatistics: async (months = 6): Promise<StatisticsData> => {
    return apiClient.get<StatisticsData>(`/dashboard/statistics?months=${months}`);
  },

  /**
   * 입찰 추적 생성/업데이트 (Upsert)
   * POST /api/v1/bids/{bid_id}/tracking
   */
  upsertTracking: async (bidId: string, data: TrackingUpsertRequest): Promise<TrackingResponse> => {
    return apiClient.post<TrackingResponse>(`/bids/${bidId}/tracking`, data);
  },

  /**
   * 입찰 추적 상태 조회
   * GET /api/v1/bids/{bid_id}/tracking
   */
  getTracking: async (bidId: string): Promise<TrackingResponse> => {
    return apiClient.get<TrackingResponse>(`/bids/${bidId}/tracking`);
  },

  /**
   * 낙찰 이력 조회
   * GET /api/v1/bids/wins
   */
  getWinHistory: async (
    params?: WinHistoryParams
  ): Promise<{ items: WinHistoryItem[]; meta: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
      startDate: params?.startDate,
      endDate: params?.endDate,
      sortBy: params?.sortBy,
      sortOrder: params?.sortOrder,
    });
    // /bids/wins는 items가 data.items에 있고 meta가 별도
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/bids/wins${query}`,
      {
        method: 'GET',
        headers: await buildAuthHeaders(),
      }
    );
    const body = (await response.json()) as {
      success: boolean;
      data?: { items?: WinHistoryItem[] };
      meta?: PaginationMeta;
      error?: { code: string; message: string };
    };
    if (!response.ok) {
      throw new Error(body.error?.message ?? '낙찰 이력을 불러올 수 없습니다.');
    }
    return {
      items: body.data?.items ?? [],
      meta: body.meta ?? { page: 1, pageSize: 20, total: 0, totalPages: 0 },
    };
  },
};

/** 인증 헤더 빌드 (apiClient 내부 함수 재사용을 위한 복사) */
async function buildAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('auth-storage');
      if (stored) {
        const parsed = JSON.parse(stored) as {
          state?: { tokens?: { accessToken?: string } };
        };
        const token = parsed?.state?.tokens?.accessToken;
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }
    } catch {
      // 토큰 파싱 실패 무시
    }
  }
  return headers;
}
