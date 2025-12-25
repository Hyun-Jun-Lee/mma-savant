"use client"

import { useSession } from "next-auth/react"
import { useEffect } from "react"
import { useAuthStore } from "@/store/authStore"
import { AuthApiService } from "@/services/authApi"

export function useAuth() {
  const { data: session, status } = useSession()
  const { user, isLoading, isAuthenticated, setUser, setLoading } = useAuthStore()

  useEffect(() => {
    // OAuth 세션 체크
    if (status === "loading") {
      setLoading(true)
      return
    }

    if (status === "authenticated" && session?.user) {
      // OAuth 로그인
      setUser({
        id: session.user.id!,
        name: session.user.name,
        email: session.user.email,
        image: session.user.image,
      })
      return
    }

    // 일반 로그인 (localStorage 토큰) 체크
    const token = AuthApiService.getToken()
    const savedUser = AuthApiService.getUser()

    if (token && savedUser) {
      setUser({
        id: String(savedUser.id),
        name: savedUser.username,
        email: savedUser.email || null,
        image: null,
      })
    } else {
      setUser(null)
    }
  }, [session, status, setUser, setLoading])

  // 일반 로그인 여부 확인
  const hasLocalToken = typeof window !== 'undefined' && AuthApiService.isAuthenticated()

  return {
    user,
    isLoading: status === "loading" || isLoading,
    isAuthenticated: (status === "authenticated" && !!session?.user) || (hasLocalToken && isAuthenticated),
    session,
  }
}
