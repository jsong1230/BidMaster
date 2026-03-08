/**
 * 멤버 관리 상태 관리 (Zustand)
 */
'use client';

import { create } from 'zustand';
import { companyApi } from '@/lib/api/company-api';
import type { Member, MemberInviteRequest } from '@/types/company';

interface MemberState {
  members: Member[];
  isLoading: boolean;
  isInviteModalOpen: boolean;
  removingMemberId: string | null;
  isInviting: boolean;
  error: string | null;
}

interface MemberActions {
  fetchMembers: (companyId: string) => Promise<void>;
  inviteMember: (companyId: string, data: MemberInviteRequest) => Promise<void>;
  removeMember: (companyId: string, memberId: string) => Promise<void>;
  openInviteModal: () => void;
  closeInviteModal: () => void;
  setRemovingId: (id: string | null) => void;
  reset: () => void;
}

const initialState: MemberState = {
  members: [],
  isLoading: false,
  isInviteModalOpen: false,
  removingMemberId: null,
  isInviting: false,
  error: null,
};

export const useMemberStore = create<MemberState & MemberActions>()((set) => ({
  ...initialState,

  fetchMembers: async (companyId: string) => {
    set({ isLoading: true, error: null });
    try {
      const result = await companyApi.listMembers(companyId);
      set({ members: result.items, isLoading: false });
    } catch (err: unknown) {
      const error = err as { message?: string };
      set({ isLoading: false, error: error?.message ?? '멤버 목록을 불러올 수 없습니다.' });
    }
  },

  inviteMember: async (companyId: string, data: MemberInviteRequest) => {
    set({ isInviting: true });
    try {
      const member = await companyApi.inviteMember(companyId, data);
      set((state) => ({
        members: [...state.members, member],
        isInviteModalOpen: false,
        isInviting: false,
      }));
    } catch (err) {
      set({ isInviting: false });
      throw err;
    }
  },

  removeMember: async (companyId: string, memberId: string) => {
    set({ removingMemberId: memberId });
    try {
      await companyApi.removeMember(companyId, memberId);
      set((state) => ({
        members: state.members.filter((m) => m.id !== memberId),
        removingMemberId: null,
      }));
    } catch (err) {
      set({ removingMemberId: null });
      throw err;
    }
  },

  openInviteModal: () => {
    set({ isInviteModalOpen: true });
  },

  closeInviteModal: () => {
    set({ isInviteModalOpen: false });
  },

  setRemovingId: (id: string | null) => {
    set({ removingMemberId: id });
  },

  reset: () => {
    set(initialState);
  },
}));
