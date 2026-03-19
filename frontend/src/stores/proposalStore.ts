/**
 * F-03 제안서 AI 초안 생성 — 제안서 상태 관리 스토어
 */

import { create } from 'zustand';
import type {
  Proposal,
  ProposalDetail,
  ProposalListParams,
  ProposalSection,
  SectionKey,
  CreateProposalRequest,
  GenerationProgress,
  RegenerateSectionRequest,
} from '@/types/proposal';
import { proposalApi } from '@/lib/api/proposal';

interface ProposalState {
  // 목록 상태
  proposals: Proposal[];
  isLoading: boolean;
  error: string | null;
  filters: ProposalListParams;

  // 상세 상태
  currentProposal: ProposalDetail | null;
  isDetailLoading: boolean;
  detailError: string | null;

  // 생성 진행 상태
  isGenerating: boolean;
  generationProgress: GenerationProgress | null;
  eventSource: EventSource | null;

  // 액션
  fetchProposals: (params?: ProposalListParams) => Promise<void>;
  fetchProposal: (id: string) => Promise<void>;
  createProposal: (data: CreateProposalRequest) => Promise<Proposal>;
  connectGenerationStream: (proposalId: string) => void;
  disconnectGenerationStream: () => void;
  updateGenerationProgress: (updater: (prev: GenerationProgress) => GenerationProgress) => void;
  regenerateSection: (
    proposalId: string,
    sectionKey: SectionKey,
    data?: RegenerateSectionRequest
  ) => Promise<ProposalSection>;
  resetDetail: () => void;
}

const initialGenerationProgress: GenerationProgress = {
  proposalId: '',
  totalSections: 0,
  completedSections: 0,
  currentSection: null,
  currentPercent: 0,
  sections: new Map(),
  error: null,
  isComplete: false,
};

export const useProposalStore = create<ProposalState>((set, get) => ({
  // 초기 상태
  proposals: [],
  isLoading: false,
  error: null,
  filters: {},

  currentProposal: null,
  isDetailLoading: false,
  detailError: null,

  isGenerating: false,
  generationProgress: null,
  eventSource: null,

  // 제안서 목록 조회
  fetchProposals: async (params?: ProposalListParams) => {
    set({ isLoading: true, error: null, filters: params || {} });
    try {
      const result = await proposalApi.list(params);
      set({ proposals: result.items, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : '제안서 목록을 불러오는데 실패했습니다.';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // 제안서 상세 조회
  fetchProposal: async (id: string) => {
    set({ isDetailLoading: true, detailError: null });
    try {
      const proposal = await proposalApi.get(id);
      set({ currentProposal: proposal, isDetailLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : '제안서 상세를 불러오는데 실패했습니다.';
      set({ detailError: message, isDetailLoading: false });
      throw error;
    }
  },

  // 제안서 생성
  createProposal: async (data: CreateProposalRequest) => {
    try {
      const result = await proposalApi.create(data);
      // 목록에 새 제안서 추가
      set((state) => ({
        proposals: [
          {
            id: result.id,
            bidId: result.bidId,
            bidTitle: null,
            title: result.title,
            status: result.status,
            version: 1,
            pageCount: 0,
            wordCount: 0,
            createdAt: result.createdAt,
            updatedAt: result.createdAt,
          },
          ...state.proposals,
        ],
      }));
      return {
        id: result.id,
        bidId: result.bidId,
        bidTitle: null,
        title: result.title,
        status: result.status,
        version: 1,
        pageCount: 0,
        wordCount: 0,
        createdAt: result.createdAt,
        updatedAt: result.createdAt,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : '제안서 생성에 실패했습니다.';
      set({ error: message });
      throw error;
    }
  },

  // SSE 스트리밍 연결
  connectGenerationStream: (proposalId: string) => {
    const eventSource = proposalApi.connectGenerateStream(proposalId);

    set({
      isGenerating: true,
      generationProgress: {
        ...initialGenerationProgress,
        proposalId,
      },
      eventSource,
    });

    // 이벤트 리스너 등록은 컴포넌트에서 처리
  },

  // 생성 진행 상태 업데이트
  updateGenerationProgress: (updater: (prev: GenerationProgress) => GenerationProgress) => {
    const { generationProgress } = get();
    if (!generationProgress) return;
    set({ generationProgress: updater(generationProgress) });
  },

  // SSE 스트리밍 연결 해제
  disconnectGenerationStream: () => {
    const { eventSource } = get();
    if (eventSource) {
      eventSource.close();
      set({
        eventSource: null,
        isGenerating: false,
        generationProgress: null,
      });
    }
  },

  // 섹션 재생성
  regenerateSection: async (
    proposalId: string,
    sectionKey: SectionKey,
    data?: RegenerateSectionRequest
  ) => {
    try {
      const result = await proposalApi.regenerateSection(proposalId, sectionKey, data || {});
      // 현재 제안서의 섹션 업데이트
      set((state) => {
        if (!state.currentProposal) return state;
        return {
          currentProposal: {
            ...state.currentProposal,
            sections: state.currentProposal.sections.map((section) =>
              section.sectionKey === sectionKey
                ? {
                    ...section,
                    title: result.title,
                    content: result.content,
                    wordCount: result.wordCount,
                    isAiGenerated: result.isAiGenerated,
                    updatedAt: result.updatedAt,
                  }
                : section
            ),
          },
        };
      });
      return {
        ...result,
        id: '',
        metadata: {},
      } as ProposalSection;
    } catch (error) {
      const message = error instanceof Error ? error.message : '섹션 재생성에 실패했습니다.';
      set({ detailError: message });
      throw error;
    }
  },

  // 상세 상태 초기화
  resetDetail: () => {
    set({
      currentProposal: null,
      isDetailLoading: false,
      detailError: null,
    });
  },
}));
