/**
 * 회사 프로필 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { companyApi } from '@/lib/api/company-api';
import type { Company, CompanyCreateRequest, CompanyUpdateRequest, MemberRole } from '@/types/company';

interface CompanyState {
  company: Company | null;
  isLoading: boolean;
  currentUserRole: MemberRole | null;
  error: string | null;
}

interface CompanyActions {
  fetchMyCompany: () => Promise<void>;
  createCompany: (data: CompanyCreateRequest) => Promise<void>;
  updateCompany: (id: string, data: CompanyUpdateRequest) => Promise<void>;
  setCurrentUserRole: (role: MemberRole | null) => void;
  reset: () => void;
}

const initialState: CompanyState = {
  company: null,
  isLoading: false,
  currentUserRole: null,
  error: null,
};

export const useCompanyStore = create<CompanyState & CompanyActions>()((set, get) => ({
  ...initialState,

  fetchMyCompany: async () => {
    set({ isLoading: true, error: null });
    try {
      const company = await companyApi.getMyCompany();
      set({ company, isLoading: false });
    } catch (err: unknown) {
      const error = err as { status?: number; message?: string };
      if (error?.status === 404) {
        // 회사 미등록 상태 — 정상
        set({ company: null, isLoading: false });
      } else {
        set({ isLoading: false, error: error?.message ?? '회사 정보를 불러올 수 없습니다.' });
      }
    }
  },

  createCompany: async (data: CompanyCreateRequest) => {
    const company = await companyApi.createCompany(data);
    set({ company, currentUserRole: 'owner' });
  },

  updateCompany: async (id: string, data: CompanyUpdateRequest) => {
    const company = await companyApi.updateCompany(id, data);
    set((state) => ({ company: { ...state.company, ...company } }));
  },

  setCurrentUserRole: (role: MemberRole | null) => {
    set({ currentUserRole: role });
  },

  reset: () => {
    set(initialState);
  },
}));

// 편의 훅: 역할 조회
export function useCurrentUserRole() {
  return useCompanyStore((s) => s.currentUserRole);
}
