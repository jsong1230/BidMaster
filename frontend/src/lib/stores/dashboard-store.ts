/**
 * F-06 입찰 현황 대시보드 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { dashboardApi } from '@/lib/api/dashboard';
import type {
  DashboardSummary,
  PipelineData,
  StatisticsData,
  TrackingStatusType,
  TrackingUpsertRequest,
} from '@/types/dashboard';

interface DashboardState {
  summary: DashboardSummary | null;
  pipeline: PipelineData | null;
  statistics: StatisticsData | null;
  isLoadingSummary: boolean;
  isLoadingPipeline: boolean;
  isLoadingStats: boolean;
  errorSummary: string | null;
  errorPipeline: string | null;
  errorStats: string | null;
  selectedPeriod: string;
  pollingIntervalId: ReturnType<typeof setInterval> | null;
}

interface DashboardActions {
  fetchSummary: (period?: string) => Promise<void>;
  fetchPipeline: () => Promise<void>;
  fetchStatistics: (months?: number) => Promise<void>;
  fetchAll: (period?: string) => Promise<void>;
  updateTrackingStatus: (bidId: string, data: TrackingUpsertRequest) => Promise<void>;
  setPeriod: (period: string) => void;
  startPolling: () => void;
  stopPolling: () => void;
}

export const useDashboardStore = create<DashboardState & DashboardActions>()((set, get) => ({
  summary: null,
  pipeline: null,
  statistics: null,
  isLoadingSummary: false,
  isLoadingPipeline: false,
  isLoadingStats: false,
  errorSummary: null,
  errorPipeline: null,
  errorStats: null,
  selectedPeriod: 'current_month',
  pollingIntervalId: null,

  fetchSummary: async (period?: string) => {
    const targetPeriod = period ?? get().selectedPeriod;
    set({ isLoadingSummary: true, errorSummary: null });
    try {
      const data = await dashboardApi.getDashboardSummary(targetPeriod);
      set({ summary: data, isLoadingSummary: false });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({
        isLoadingSummary: false,
        errorSummary: error?.message ?? '데이터를 불러올 수 없습니다.',
      });
    }
  },

  fetchPipeline: async () => {
    set({ isLoadingPipeline: true, errorPipeline: null });
    try {
      const data = await dashboardApi.getDashboardPipeline();
      set({ pipeline: data, isLoadingPipeline: false });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({
        isLoadingPipeline: false,
        errorPipeline: error?.message ?? '데이터를 불러올 수 없습니다.',
      });
    }
  },

  fetchStatistics: async (months = 6) => {
    set({ isLoadingStats: true, errorStats: null });
    try {
      const data = await dashboardApi.getDashboardStatistics(months);
      set({ statistics: data, isLoadingStats: false });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({
        isLoadingStats: false,
        errorStats: error?.message ?? '데이터를 불러올 수 없습니다.',
      });
    }
  },

  fetchAll: async (period?: string) => {
    const targetPeriod = period ?? get().selectedPeriod;
    // 3개 API 병렬 호출
    await Promise.all([
      get().fetchSummary(targetPeriod),
      get().fetchPipeline(),
      get().fetchStatistics(6),
    ]);
  },

  /**
   * 입찰 추적 상태 변경 (낙관적 업데이트)
   * 1. 즉시 파이프라인 UI 업데이트
   * 2. API 호출
   * 3. 성공 시 최신 파이프라인 재조회
   * 4. 실패 시 롤백
   */
  updateTrackingStatus: async (bidId: string, data: TrackingUpsertRequest) => {
    const prevPipeline = get().pipeline;

    // 낙관적 업데이트: 아이템을 새 상태 컬럼으로 이동
    if (prevPipeline) {
      const newStages = prevPipeline.stages.map((stage) => {
        // 현재 단계에서 아이템 제거
        const filteredItems = stage.items.filter((item) => item.bidId !== bidId);
        // 새 단계에 아이템 추가
        if (stage.status === data.status) {
          const movedItem = prevPipeline.stages
            .flatMap((s) => s.items)
            .find((item) => item.bidId === bidId);
          if (movedItem) {
            return {
              ...stage,
              count: filteredItems.length + 1,
              items: [...filteredItems, { ...movedItem, updatedAt: new Date().toISOString() }],
            };
          }
        }
        return {
          ...stage,
          count: filteredItems.length,
          items: filteredItems,
        };
      });
      set({ pipeline: { stages: newStages } });
    }

    try {
      await dashboardApi.upsertTracking(bidId, data);
      // 최신 상태 재조회
      await get().fetchPipeline();
    } catch (err: unknown) {
      // 실패 시 롤백
      set({ pipeline: prevPipeline });
      throw err;
    }
  },

  setPeriod: (period: string) => {
    set({ selectedPeriod: period });
    get().fetchSummary(period);
  },

  startPolling: () => {
    const { pollingIntervalId } = get();
    if (pollingIntervalId) return; // 이미 실행 중

    const intervalId = setInterval(() => {
      // 탭 비활성 시 폴링 중지
      if (document.hidden) return;
      get().fetchSummary();
      get().fetchPipeline();
    }, 30_000);

    // 탭 활성화 시 즉시 1회 호출
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        get().fetchSummary();
        get().fetchPipeline();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    set({ pollingIntervalId: intervalId });
  },

  stopPolling: () => {
    const { pollingIntervalId } = get();
    if (pollingIntervalId) {
      clearInterval(pollingIntervalId);
      set({ pollingIntervalId: null });
    }
  },
}));

/** 파이프라인 상태 레이블 매핑 */
export const PIPELINE_STATUS_LABELS: Record<TrackingStatusType, string> = {
  interested: '관심',
  participating: '참여',
  submitted: '제출',
  won: '낙찰',
  lost: '실패',
};

/** 파이프라인 상태 색상 (Tailwind 클래스) */
export const PIPELINE_STATUS_COLORS: Record<
  TrackingStatusType,
  { border: string; badge: string; text: string }
> = {
  interested: {
    border: 'border-t-[#2196F3]',
    badge: 'bg-blue-50 text-blue-700',
    text: 'text-blue-600',
  },
  participating: {
    border: 'border-t-[#627D98]',
    badge: 'bg-[#F0F4F8] text-[#486581]',
    text: 'text-[#627D98]',
  },
  submitted: {
    border: 'border-t-[#FFC107]',
    badge: 'bg-amber-50 text-amber-700',
    text: 'text-amber-600',
  },
  won: {
    border: 'border-t-[#4CAF50]',
    badge: 'bg-green-50 text-green-700',
    text: 'text-green-600',
  },
  lost: {
    border: 'border-t-[#F44336]',
    badge: 'bg-red-50 text-red-700',
    text: 'text-red-600',
  },
};

/** 기간 선택 옵션 */
export const PERIOD_OPTIONS = [
  { value: 'current_month', label: '이번 달' },
  { value: 'last_month', label: '지난 달' },
  { value: 'last_3_months', label: '최근 3개월' },
  { value: 'last_6_months', label: '최근 6개월' },
  { value: 'last_year', label: '최근 1년' },
];
