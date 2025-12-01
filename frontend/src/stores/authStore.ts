/**
 * Authentication Store
 * Zustand store for managing authentication state
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  user_id: string
  username: string
  email: string
  full_name: string
  role: 'admin' | 'engineer' | 'viewer'
  is_active: boolean
}

interface AuthState {
  // State
  token: string | null
  refreshToken: string | null
  user: User | null
  isAuthenticated: boolean

  // Actions
  login: (token: string, refreshToken: string, user: User) => void
  logout: () => void
  setToken: (token: string) => void
  setUser: (user: User) => void

  // Helpers
  isAdmin: () => boolean
  isEngineer: () => boolean
  canWrite: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      // Actions
      login: (token, refreshToken, user) => {
        set({
          token,
          refreshToken,
          user,
          isAuthenticated: true,
        })
      },

      logout: () => {
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        })
      },

      setToken: (token) => {
        set({ token })
      },

      setUser: (user) => {
        set({ user })
      },

      // Helper methods
      isAdmin: () => {
        const { user } = get()
        return user?.role === 'admin'
      },

      isEngineer: () => {
        const { user } = get()
        return user?.role === 'engineer'
      },

      canWrite: () => {
        const { user } = get()
        return user?.role === 'admin' || user?.role === 'engineer'
      },
    }),
    {
      name: 'battery-rul-auth', // localStorage key
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
