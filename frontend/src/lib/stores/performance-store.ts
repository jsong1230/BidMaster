/**
 * 수행 실적 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { companyApi } from '@/lib/api/company-api';
import type { Performance, PerformanceCreateRequest, PerformanceUpdateRequest, ListPerformancesParams } from '@/types/company';

interface PerformanceState {
  performances: Performance[];
  isLoading: boolean;
  isSlideOverOpen: boolean;
  editingPerformance: Performance | null;
  deletingPerformanceId: string | null;
  representativeCount: number;
  filterStatus: 'all' | 'completed' | 'ongoing';
  error: string | null;
}

interface PerformanceActions {
  fetchPerformances: (companyId: string, params?: ListPerformancesParams) => Promise<void>;
  createPerformance: (companyId: string, data: PerformanceCreateRequest) => Promise<void>;
  updatePerformance: (companyId: string, perfId: string, data: PerformanceUpdateRequest) => Promise<void>;
  deletePerformance: (companyId: string, perfId: string) => Promise<void>;
  setRepresentative: (companyId: string, perfId: string, isRepresentative: boolean) => Promise<void>;
  openSlideOver: (performance?: Performance) => void;
  closeSlideOver: () => void;
  setDeletingId: (id: string | null) => void;
  setFilterStatus: (status: 'all' | 'completed' | 'ongoing') => void;
  reset: () => void;
}

const initialState: PerformanceState = {
  performances: [],
  isLoading: false,
  isSlideOverOpen: false,
  editingPerformance: null,
  deletingPerformanceId: null,
  representativeCount: 0,
  filterStatus: 'all',
  error: null,
};

export const usePerformanceStore = create<PerformanceState & PerformanceActions>()((set, get) => ({
  ...initialState,

  fetchPerformances: async (companyId: string, params?: ListPerformancesParams) => {
    set({ isLoading: true, error: null });
    try {
      const result = await companyApi.listPerformances(companyId, params);
      const repCount = result.items.filter((p) => p.isRepresentative).length;
      set({
        performances: result.items,
        representativeCount: repCount,
        isLoading: false,
      });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({ isLoading: false, error: error?.message ?? '실적 목록을 불러올 수 없습니다.' });
    }
  },

  createPerformance: async (companyId: string, data: PerformanceCreateRequest) => {
    const perf = await companyApi.createPerformance(companyId, data);
    set((state) => {
      const updated = [perf, ...state.performances];
      const repCount = updated.filter((p) => p.isRepresentative).length;
      return { performances: updated, representativeCount: repCount };
    });
  },

  updatePerformance: async (companyId: string, perfId: string, data: PerformanceUpdateRequest) => {
    const updated = await companyApi.updatePerformance(companyId, perfId, data);
    set((state) => {
      const performances = state.performances.map((p) => (p.id === perfId ? updated : p));
      const repCount = performances.filter((p) => p.isRepresentative).length;
      return { performances, representativeCount: repCount };
    });
  },

  deletePerformance: async (companyId: string, perfId: string) => {
    await companyApi.deletePerformance(companyId, perfId);
    set((state) => {
      const performances = state.performances.filter((p) => p.id !== perfId);
      const repCount = performances.filter((p) => p.isRepresentative).length;
      return { performances, representativeCount: repCount, deletingPerformanceId: null };
    });
  },

  setRepresentative: async (companyId: string, perfId: string, isRepresentative: boolean) => {
    // 낙관적 업데이트
    set((state) => {
      const performances = state.performances.map((p) =>
        p.id === perfId ? { ...p, isRepresentative } : p
      );
      const repCount = performances.filter((p) => p.isRepresentative).length;
      return { performances, representativeCount: repCount };
    });

    try {
      const updated = await companyApi.setRepresentative(companyId, perfId, isRepresentative);
      set((state) => {
        const performances = state.performances.map((p) => (p.id === perfId ? updated : p));
        const repCount = performances.filter((p) => p.isRepresentative).length;
        return { performances, representativeCount: repCount };
      });
    } catch (err) {
      // 롤백
      set((state) => {
        const performances = state.performances.map((p) =>
          p.id === perfId ? { ...p, isRepresentative: !isRepresentative } : p
        );
        const repCount = performances.filter((p) => p.isRepresentative).length;
        return { performances, representativeCount: repCount };
      });
      throw err;
    }
  },

  openSlideOver: (performance?: Performance) => {
    set({ isSlideOverOpen: true, editingPerformance: performance ?? null });
  },

  closeSlideOver: () => {
    set({ isSlideOverOpen: false, editingPerformance: null });
  },

  setDeletingId: (id: string | null) => {
    set({ deletingPerformanceId: id });
  },

  setFilterStatus: (status: 'all' | 'completed' | 'ongoing') => {
    set({ filterStatus: status });
  },

  reset: () => {
    set(initialState);
  },
}));
