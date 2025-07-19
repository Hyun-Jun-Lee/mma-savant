import { create } from 'zustand'
import { AuthUser, AuthState } from '@/types/auth'

interface AuthStore extends AuthState {
  setUser: (user: AuthUser | null) => void
  setLoading: (loading: boolean) => void
  login: (user: AuthUser) => void
  logout: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  
  setUser: (user) =>
    set({
      user,
      isAuthenticated: !!user,
      isLoading: false,
    }),
    
  setLoading: (isLoading) =>
    set({ isLoading }),
    
  login: (user) =>
    set({
      user,
      isAuthenticated: true,
      isLoading: false,
    }),
    
  logout: () =>
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    }),
}))