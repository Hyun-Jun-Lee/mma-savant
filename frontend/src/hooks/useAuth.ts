"use client"

import { useSession } from "next-auth/react"
import { useEffect } from "react"
import { useAuthStore } from "@/store/authStore"

export function useAuth() {
  const { data: session, status } = useSession()
  const { user, isLoading, isAuthenticated, setUser, setLoading } = useAuthStore()

  useEffect(() => {
    if (status === "loading") {
      setLoading(true)
    } else if (status === "authenticated" && session?.user) {
      setUser({
        id: session.user.id!,
        name: session.user.name,
        email: session.user.email,
        image: session.user.image,
      })
    } else {
      setUser(null)
    }
  }, [session, status, setUser, setLoading])

  return {
    user,
    isLoading: status === "loading" || isLoading,
    isAuthenticated: status === "authenticated" && isAuthenticated,
    session,
  }
}