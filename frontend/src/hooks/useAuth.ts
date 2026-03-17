"use client"

import { useSession } from "next-auth/react"
import { useEffect, useRef } from "react"
import { useAuthStore } from "@/store/authStore"
import { AuthApiService } from "@/services/authApi"

export function useAuth() {
  const { data: session, status } = useSession()
  const { user, isLoading, isAuthenticated, setUser, setLoading } = useAuthStore()
  const lastUserIdRef = useRef<string | null>(null)

  useEffect(() => {
    // OAuth 세션 체크
    if (status === "loading") {
      setLoading(true)
      return
    }

    if (status === "authenticated" && session?.user) {
      const id = session.user.id!
      // 이미 같은 유저가 설정되어 있으면 skip (참조 변경 방지)
      if (lastUserIdRef.current === id) return
      lastUserIdRef.current = id
      setUser({
        id,
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
      const id = String(savedUser.id)
      if (lastUserIdRef.current === id) return
      lastUserIdRef.current = id
      setUser({
        id,
        name: savedUser.username,
        email: savedUser.email || null,
        image: null,
      })
    } else {
      lastUserIdRef.current = null
      setUser(null)
    }
  }, [session, status, setUser, setLoading, user])

  // 일반 로그인 여부 확인
  const hasLocalToken = typeof window !== 'undefined' && AuthApiService.isAuthenticated()

  return {
    user,
    isLoading: status === "loading" || isLoading,
    isAuthenticated: (status === "authenticated" && !!session?.user) || (hasLocalToken && isAuthenticated),
    session,
  }
}
