/**
 * HTTP API 클라이언트
 * 모든 API 요청에 인증 헤더를 자동으로 포함
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class HttpError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

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

async function buildHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new HttpError(response.status, 'PARSE_ERROR', '응답을 파싱할 수 없습니다.');
  }

  if (!response.ok) {
    const errorBody = body as { error?: { code?: string; message?: string }; detail?: string };
    const code = errorBody?.error?.code ?? 'UNKNOWN';
    const message = errorBody?.error?.message ?? errorBody?.detail ?? '요청에 실패했습니다.';
    throw new HttpError(response.status, code, message);
  }

  const successBody = body as { success?: boolean; data?: T };
  return (successBody?.data ?? body) as T;
}

async function buildListResponse<T>(response: Response): Promise<{ items: T[]; meta?: PaginationMeta }> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new HttpError(response.status, 'PARSE_ERROR', '응답을 파싱할 수 없습니다.');
  }

  if (!response.ok) {
    const errorBody = body as { error?: { code?: string; message?: string }; detail?: string };
    const code = errorBody?.error?.code ?? 'UNKNOWN';
    const message = errorBody?.error?.message ?? errorBody?.detail ?? '요청에 실패했습니다.';
    throw new HttpError(response.status, code, message);
  }

  const successBody = body as {
    success?: boolean;
    data?: { items?: T[] };
    meta?: PaginationMeta;
  };
  return {
    items: successBody?.data?.items ?? [],
    meta: successBody?.meta,
  };
}

export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export const apiClient = {
  get: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: await buildHeaders(),
    });
    return handleResponse<T>(response);
  },

  getList: async <T>(endpoint: string): Promise<{ items: T[]; meta?: PaginationMeta }> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: await buildHeaders(),
    });
    return buildListResponse<T>(response);
  },

  post: async <T>(endpoint: string, data?: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: await buildHeaders(),
      body: data !== undefined ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  put: async <T>(endpoint: string, data?: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: await buildHeaders(),
      body: data !== undefined ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  patch: async <T>(endpoint: string, data?: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers: await buildHeaders(),
      body: data !== undefined ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  delete: async <T = null>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: await buildHeaders(),
    });
    return handleResponse<T>(response);
  },
};
