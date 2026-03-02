/**
 * 인증 상태 관리 (Zustand)
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import { authApi, User, Tokens } from '@/lib/api/auth';

interface AuthState {
  user: User | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  loginWithKakao: () => void;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  initialize: () => Promise<void>;
  updateTokens: (tokens: Tokens) => void;
}

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      // 상태
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: true,
      isInitialized: false,

      // 액션
      login: async (email: string, password: string) => {
        try {
          set({ isLoading: true });
          const response = await authApi.login({ email, password });
          set({
            user: response.user,
            tokens: response.tokens,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
            set({ isLoading: false });
            throw error;
        }
      },

      loginWithKakao: () => {
        // 카카오 로그인 URL로 리다이렉트
        const redirectUrl = encodeURIComponent(window.location.origin + '/auth/callback');
        window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/oauth/kakao?redirect_url=${redirectUrl}`;
      },

      logout: async () => {
        try {
          const { tokens } = get();
          if (tokens?.refreshToken) {
            await authApi.logout(tokens.refreshToken);
          }
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
        }
      },

      refreshTokens: async () => {
        const { tokens } = get();
        if (!tokens?.refreshToken) {
          throw new Error('No refresh token');
        }

        try {
          const newTokens = await authApi.refreshToken(tokens.refreshToken);
          set({ tokens: newTokens });
        } catch (error) {
          // 리프레시 토큰도 만료된 경우 로그아웃
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      setUser: (user: User | null) => {
        set({
          user,
          isAuthenticated: !!user,
        });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      initialize: async () => {
        const { tokens } = get();
        if (!tokens?.accessToken) {
          set({ isLoading: false, isInitialized: true });
          return;
        }

        try {
          const user = await authApi.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true,
          });
        } catch (error) {
          // 액세스 토큰 만료 시 리프레시 시도
          try {
            await get().refreshTokens();
            const user = await authApi.getCurrentUser();
            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              isInitialized: true,
            });
          } catch {
            set({
              user: null,
              tokens: null,
              isAuthenticated: false,
              isLoading: false,
              isInitialized: true,
            });
          }
        }
      },

      updateTokens: (tokens: Tokens) => {
        set({ tokens });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        tokens: state.tokens,
      }),
    }
  )
);
