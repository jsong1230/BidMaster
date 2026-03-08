/**
 * 공고 목록 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { bidsApi } from '@/lib/api/bids';
import type { BidItem, BidListParams } from '@/types/bid';
import type { PaginationMeta } from '@/lib/api/client';

interface BidFilters {
  keyword: string;
  status: string;
  category: string;
  region: string;
  minBudget: number | null;
  maxBudget: number | null;
  sortBy: 'deadline' | 'announcementDate' | 'budget' | 'createdAt';
  sortOrder: 'asc' | 'desc';
}

interface BidState {
  bids: BidItem[];
  isLoading: boolean;
  error: string | null;
  pagination: PaginationMeta;
  filters: BidFilters;
  currentPage: number;
}

interface BidActions {
  fetchBids: (page?: number) => Promise<void>;
  setFilter: (key: keyof BidFilters, value: BidFilters[keyof BidFilters]) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
}

const defaultFilters: BidFilters = {
  keyword: '',
  status: '',
  category: '',
  region: '',
  minBudget: null,
  maxBudget: null,
  sortBy: 'deadline',
  sortOrder: 'asc',
};

const defaultPagination: PaginationMeta = {
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
};

export const useBidStore = create<BidState & BidActions>()((set, get) => ({
  bids: [],
  isLoading: false,
  error: null,
  pagination: defaultPagination,
  filters: defaultFilters,
  currentPage: 1,

  fetchBids: async (page?: number) => {
    set({ isLoading: true, error: null });
    const { filters, currentPage } = get();
    const targetPage = page ?? currentPage;

    try {
      const params: BidListParams = {
        page: targetPage,
        pageSize: 20,
        keyword: filters.keyword || undefined,
        status: (filters.status as BidListParams['status']) || undefined,
        category: filters.category || undefined,
        region: filters.region || undefined,
        minBudget: filters.minBudget ?? undefined,
        maxBudget: filters.maxBudget ?? undefined,
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
      };
      const { items, meta } = await bidsApi.getBids(params);
      set({ bids: items, pagination: meta, currentPage: targetPage, isLoading: false });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({ isLoading: false, error: error?.message ?? '공고 목록을 불러올 수 없습니다.' });
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
