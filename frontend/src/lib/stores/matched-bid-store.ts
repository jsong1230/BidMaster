/**
 * 매칭 공고 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { bidsApi } from '@/lib/api/bids';
import type { MatchedBidItem, MatchedBidListParams, RecommendationType } from '@/types/bid-match';
import type { PaginationMeta } from '@/lib/api/client';

interface MatchedBidFilters {
  recommendation: 'all' | RecommendationType;
  minScore: number;
  sortBy: 'totalScore' | 'analyzedAt' | 'deadline';
  sortOrder: 'asc' | 'desc';
}

interface MatchedBidState {
  matches: MatchedBidItem[];
  isLoading: boolean;
  error: string | null;
  hasCompanyProfile: boolean;
  pagination: PaginationMeta;
  filters: MatchedBidFilters;
  currentPage: number;
}

interface MatchedBidActions {
  fetchMatchedBids: (page?: number) => Promise<void>;
  setFilter: (key: keyof MatchedBidFilters, value: MatchedBidFilters[keyof MatchedBidFilters]) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
}

const defaultFilters: MatchedBidFilters = {
  recommendation: 'all',
  minScore: 0,
  sortBy: 'totalScore',
  sortOrder: 'desc',
};

const defaultPagination: PaginationMeta = {
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
};

export const useMatchedBidStore = create<MatchedBidState & MatchedBidActions>()((set, get) => ({
  matches: [],
  isLoading: false,
  error: null,
  hasCompanyProfile: true,
  pagination: defaultPagination,
  filters: defaultFilters,
  currentPage: 1,

  fetchMatchedBids: async (page?: number) => {
    set({ isLoading: true, error: null });
    const { filters, currentPage } = get();
    const targetPage = page ?? currentPage;

    try {
      const params: MatchedBidListParams = {
        page: targetPage,
        pageSize: 20,
        minScore: filters.minScore > 0 ? filters.minScore : undefined,
        recommendation: filters.recommendation !== 'all' ? filters.recommendation : 'all',
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
      };
      const { items, meta } = await bidsApi.getMatchedBids(params);
      set({
        matches: items,
        pagination: meta,
        currentPage: targetPage,
        isLoading: false,
        hasCompanyProfile: true,
      });
    } catch (err: unknown) {
      const error = err as { code?: string; message?: string };
      if (error?.code === 'COMPANY_001') {
        set({ isLoading: false, hasCompanyProfile: false, matches: [] });
      } else {
        set({ isLoading: false, error: error?.message ?? '매칭 공고를 불러올 수 없습니다.' });
      }
    }
  },

  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      currentPage: 1,
    }));
  },

  resetFilters: () => {
    set({ filters: defaultFilters, currentPage: 1 });
  },

  setPage: (page) => {
    set({ currentPage: page });
  },
}));
