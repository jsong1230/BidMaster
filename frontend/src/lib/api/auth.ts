/**
 * 인증 API 클라이언트
 */
import { apiClient } from './client';

// === 타입 정의 ===

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  phone?: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  companyId?: string;
  role: string;
  isNewUser: boolean;
  createdAt: string;
}

export interface Tokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginResponse {
  user: User;
  tokens: Tokens;
}

export interface RefreshTokenResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// === API 함수 ===

export const authApi = {
  /**
   * 로그인
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/login', data);
  },

  /**
   * 회원가입
   */
  register: async (data: RegisterRequest): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/register', data);
  },

  /**
   * 로그아웃
   */
  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/auth/logout', { refreshToken });
  },

  /**
   * 토큰 갱신
   */
  refreshToken: async (refreshToken: string): Promise<RefreshTokenResponse> => {
    return apiClient.post<RefreshTokenResponse>('/auth/refresh', { refreshToken });
  },

  /**
   * 현재 사용자 정보 조회
   */
  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * 비밀번호 변경
   */
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/change-password', { currentPassword, newPassword });
  },

  /**
   * 비밀번호 찾기
   */
  forgotPassword: async (email: string): Promise<{ message: string }> => {
    return apiClient.post<{ message: string }>('/auth/forgot-password', { email });
  },

  /**
   * 비밀번호 재설정
   */
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/reset-password', { token, newPassword });
  },

  /**
   * 계정 탈퇴
   */
  deleteAccount: async (password: string): Promise<void> => {
    await apiClient.delete('/auth/me');
  },
};
