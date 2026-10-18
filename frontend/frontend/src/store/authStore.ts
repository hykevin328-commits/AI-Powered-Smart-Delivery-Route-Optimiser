import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, TokenResponse } from '@/types'
import apiClient from '@/lib/axios'

// ── Guest user (no backend required) ─────────────────────────────────────────
export const GUEST_USER: User = {
  id: 'guest-00000000-0000-0000-0000-000000000000',
  full_name: 'Guest User',
  email: 'guest@demo.local',
  phone: null,
  role: 'admin',
  is_active: true,
  is_verified: true,
  avatar_url: null,
  address: null,
  licence_number: null,
  last_login_at: null,
  created_at: new Date().toISOString(),
}

export const GUEST_TOKENS: TokenResponse = {
  access_token: 'guest-token',
  refresh_token: 'guest-refresh-token',
  token_type: 'bearer',
  expires_in: 86400,
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isGuest: boolean

  setAuth: (user: User, tokens: TokenResponse) => void
  loginAsGuest: () => void
  setUser: (user: User) => void
  logout: () => void
  setLoading: (v: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      isGuest: false,

      setAuth: (user, tokens) => {
        localStorage.setItem('access_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)
        apiClient.defaults.headers.common.Authorization = `Bearer ${tokens.access_token}`
        set({
          user,
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
          isGuest: false,
        })
      },

      loginAsGuest: () => {
        localStorage.setItem('access_token', GUEST_TOKENS.access_token)
        localStorage.setItem('refresh_token', GUEST_TOKENS.refresh_token)
        set({
          user: GUEST_USER,
          accessToken: GUEST_TOKENS.access_token,
          refreshToken: GUEST_TOKENS.refresh_token,
          isAuthenticated: true,
          isGuest: true,
        })
      },

      setUser: (user) => set({ user }),

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        delete apiClient.defaults.headers.common.Authorization
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isGuest: false,
        })
      },

      setLoading: (v) => set({ isLoading: v }),
    }),
    {
      name: 'auth-storage',
      partialize: (s) => ({
        user: s.user,
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        isAuthenticated: s.isAuthenticated,
        isGuest: s.isGuest,
      }),
    },
  ),
)
