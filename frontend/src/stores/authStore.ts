import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '@/lib/types';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: UserResponse | null;
  isAuthenticated: boolean;
  login: (token: string, refreshToken: string, user: UserResponse) => void;
  setTokens: (token: string, refreshToken?: string | null) => void;
  logout: () => void;
  setUser: (user: UserResponse) => void;
}

export const useAuthStore = create<AuthState>()(persist((set) => ({
  token: null, refreshToken: null, user: null, isAuthenticated: false,
  login: (token, refreshToken, user) => {
    if (typeof document !== 'undefined') document.cookie = `auth-token=${token}; path=/`;
    set({ token, refreshToken, user, isAuthenticated: true });
  },
  setTokens: (token, refreshToken) => {
    if (typeof document !== 'undefined') document.cookie = `auth-token=${token}; path=/`;
    set((state) => ({
      token,
      refreshToken: refreshToken ?? state.refreshToken,
      isAuthenticated: true,
    }));
  },
  logout: () => {
    if (typeof document !== 'undefined') document.cookie = 'auth-token=; Max-Age=0; path=/';
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
  },
  setUser: (user) => set({ user, isAuthenticated: true }),
}), { name: 'auth-store' }));
