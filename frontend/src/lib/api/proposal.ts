/**
 * F-03 제안서 AI 초안 생성 — 제안서 API 클라이언트
 */

import type {
  Proposal,
  ProposalDetail,
  ProposalListParams,
  ProposalListResponse,
  CreateProposalRequest,
  CreateProposalResponse,
  RegenerateSectionRequest,
  RegenerateSectionResponse,
  DownloadFormat,
  DownloadResponse,
  SSEEvent,
} from '@/types/proposal';
export type { SSEEvent } from '@/types/proposal';
import { apiClient } from './client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ========== API 클라이언트 ==========

export const proposalApi = {
  /**
   * 제안서 목록 조회
   */
  list: async (params?: ProposalListParams): Promise<ProposalListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.pageSize) searchParams.append('pageSize', params.pageSize.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.bidId) searchParams.append('bidId', params.bidId);
    if (params?.sortBy) searchParams.append('sortBy', params.sortBy);
    if (params?.sortOrder) searchParams.append('sortOrder', params.sortOrder);

    const query = searchParams.toString();
    const endpoint = query ? `/proposals?${query}` : '/proposals';
    return apiClient.getList<Proposal>(endpoint);
  },

  /**
   * 제안서 상세 조회
   */
  get: async (id: string): Promise<ProposalDetail> => {
    return apiClient.get<ProposalDetail>(`/proposals/${id}`);
  },

  /**
   * 제안서 생성
   */
  create: async (data: CreateProposalRequest): Promise<CreateProposalResponse> => {
    return apiClient.post<CreateProposalResponse>('/proposals', data);
  },

  /**
   * SSE 스트리밍 연결 (제안서 생성 진행)
   */
  connectGenerateStream: (proposalId: string): EventSource => {
    // 토큰을 query parameter로 전달 (SSE는 헤더 전달 불가)
    const token = getAccessToken();
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    const url = `${API_BASE_URL}/proposals/${proposalId}/generate/stream${tokenParam}`;
    return new EventSource(url);
  },

  /**
   * 섹션 재생성
   */
  regenerateSection: async (
    proposalId: string,
    sectionKey: string,
    data: RegenerateSectionRequest
  ): Promise<RegenerateSectionResponse> => {
    return apiClient.post<RegenerateSectionResponse>(
      `/proposals/${proposalId}/sections/${sectionKey}/regenerate`,
      data
    );
  },

  /**
   * 제안서 다운로드
   */
  download: async (proposalId: string, format: DownloadFormat): Promise<DownloadResponse> => {
    const token = getAccessToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_BASE_URL}/proposals/${proposalId}/download?format=${format}`,
      {
        method: 'GET',
        headers,
      }
    );

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const message = errorBody?.error?.message || errorBody?.detail || '다운로드에 실패했습니다.';
      throw new Error(message);
    }

    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `proposal.${format}`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (match?.[1]) {
        filename = match[1].replace(/['"]/g, '');
      }
    }

    const data = await response.blob();

    return {
      filename,
      contentType: response.headers.get('Content-Type') || '',
      data,
    };
  },
};

// ========== 유틸리티 ==========

/**
 * 액세스 토큰 가져오기
 */
function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem('auth-storage');
    if (!stored) return null;
    const parsed = JSON.parse(stored) as { state?: { tokens?: { accessToken?: string } } };
    return parsed?.state?.tokens?.accessToken ?? null;
  } catch {
    return null;
  }
}

// ========== SSE 파서 ==========

/**
 * SSE 이벤트 파싱
 */
export function parseSSEEvent(message: string): SSEEvent | null {
  try {
    const lines = message.trim().split('\n');
    let eventType: SSEEvent['event'] | null = null;
    let dataStr = '';

    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventType = line.substring(6).trim() as SSEEvent['event'];
      } else if (line.startsWith('data:')) {
        dataStr = line.substring(5).trim();
      }
    }

    if (!eventType || !dataStr) {
      return null;
    }

    const data = JSON.parse(dataStr);

    switch (eventType) {
      case 'start':
        return { event: 'start', data };
      case 'progress':
        return { event: 'progress', data };
      case 'section':
        return { event: 'section', data };
      case 'complete':
        return { event: 'complete', data };
      case 'error':
        return { event: 'error', data };
      default:
        return null;
    }
  } catch {
    return null;
  }
}
