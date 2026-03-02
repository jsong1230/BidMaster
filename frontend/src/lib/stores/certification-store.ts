/**
 * 보유 인증 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { companyApi } from '@/lib/api/company-api';
import type { Certification, CertificationCreateRequest, CertificationUpdateRequest } from '@/types/company';

interface CertificationState {
  certifications: Certification[];
  isLoading: boolean;
  isModalOpen: boolean;
  editingCert: Certification | null;
  deletingCertId: string | null;
  error: string | null;
}

interface CertificationActions {
  fetchCertifications: (companyId: string) => Promise<void>;
  createCertification: (companyId: string, data: CertificationCreateRequest) => Promise<void>;
  updateCertification: (companyId: string, certId: string, data: CertificationUpdateRequest) => Promise<void>;
  deleteCertification: (companyId: string, certId: string) => Promise<void>;
  openModal: (cert?: Certification) => void;
  closeModal: () => void;
  setDeletingId: (id: string | null) => void;
  reset: () => void;
}

const initialState: CertificationState = {
  certifications: [],
  isLoading: false,
  isModalOpen: false,
  editingCert: null,
  deletingCertId: null,
  error: null,
};

export const useCertificationStore = create<CertificationState & CertificationActions>()(
  (set) => ({
    ...initialState,

    fetchCertifications: async (companyId: string) => {
      set({ isLoading: true, error: null });
      try {
        const result = await companyApi.listCertifications(companyId);
        set({ certifications: result.items, isLoading: false });
      } catch (err: unknown) {
        const error = err as { message?: string };
        set({ isLoading: false, error: error?.message ?? '인증 목록을 불러올 수 없습니다.' });
      }
    },

    createCertification: async (companyId: string, data: CertificationCreateRequest) => {
      const cert = await companyApi.createCertification(companyId, data);
      set((state) => ({ certifications: [cert, ...state.certifications] }));
    },

    updateCertification: async (
      companyId: string,
      certId: string,
      data: CertificationUpdateRequest
    ) => {
      const updated = await companyApi.updateCertification(companyId, certId, data);
      set((state) => ({
        certifications: state.certifications.map((c) => (c.id === certId ? updated : c)),
      }));
    },

    deleteCertification: async (companyId: string, certId: string) => {
      await companyApi.deleteCertification(companyId, certId);
      set((state) => ({
        certifications: state.certifications.filter((c) => c.id !== certId),
        deletingCertId: null,
      }));
    },

    openModal: (cert?: Certification) => {
      set({ isModalOpen: true, editingCert: cert ?? null });
    },

    closeModal: () => {
      set({ isModalOpen: false, editingCert: null });
    },

    setDeletingId: (id: string | null) => {
      set({ deletingCertId: id });
    },

    reset: () => {
      set(initialState);
    },
  })
);
