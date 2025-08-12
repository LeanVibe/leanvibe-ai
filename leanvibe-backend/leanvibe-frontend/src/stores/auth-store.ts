import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User, LoginRequest, RegisterRequest } from '@/types/api'
import { apiClient } from '@/lib/api-client'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  getCurrentUser: () => Promise<void>
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.login(credentials)
          
          // Store refresh token
          if (typeof window !== 'undefined') {
            localStorage.setItem('refresh_token', response.refresh_token)
          }
          
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null
          })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed'
          set({ 
            error: errorMessage, 
            isLoading: false,
            isAuthenticated: false,
            user: null
          })
          throw error
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.register(data)
          
          // Store refresh token
          if (typeof window !== 'undefined') {
            localStorage.setItem('refresh_token', response.refresh_token)
          }
          
          set({ 
            user: response.user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null
          })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Registration failed'
          set({ 
            error: errorMessage, 
            isLoading: false,
            isAuthenticated: false,
            user: null
          })
          throw error
        }
      },

      logout: async () => {
        set({ isLoading: true, error: null })
        
        try {
          await apiClient.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null
          })
        }
      },

      refreshToken: async () => {
        try {
          const response = await apiClient.refreshToken()
          
          // Store new refresh token
          if (typeof window !== 'undefined') {
            localStorage.setItem('refresh_token', response.refresh_token)
          }
          
          set({ 
            user: response.user, 
            isAuthenticated: true,
            error: null
          })
        } catch (error) {
          console.error('Token refresh failed:', error)
          // If refresh fails, logout the user
          get().logout()
          throw error
        }
      },

      getCurrentUser: async () => {
        set({ isLoading: true, error: null })
        
        try {
          const user = await apiClient.getCurrentUser()
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null
          })
        } catch (error) {
          console.error('Get current user failed:', error)
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: 'Failed to get user information'
          })
          throw error
        }
      },

      clearError: () => {
        set({ error: null })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)